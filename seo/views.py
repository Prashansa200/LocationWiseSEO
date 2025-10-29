from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from geopy.geocoders import Nominatim
import requests
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Replace with your actual SerpApi key
SERP_API_KEY = "a04b84ffd85845896112362caa545b2a4cf79a448cb0f0050cb3bae33232a230"

# ---------- Helper function: Convert coords to city/region/country ----------
def coords_to_place(lat, lon):
    geolocator = Nominatim(user_agent="my_test_app_prashansa_2025")
    try:
        location = geolocator.reverse((lat, lon), language='en', timeout=10)
        if location:
            print("📍 Raw Location Data:", location.raw)
            addr = location.raw.get('address', {})
            return {
                'city': (
                    addr.get('city') or addr.get('town') or addr.get('village') or
                    addr.get('hamlet') or addr.get('municipality') or addr.get('county') or addr.get('suburb')
                ),
                'region': (
                    addr.get('state') or addr.get('region') or
                    addr.get('state_district') or addr.get('province')
                ),
                'country': addr.get('country') or addr.get('country_code')
            }
    except Exception as e:
        print("⚠️ Geocoding error:", e)
    return {'city': None, 'region': None, 'country': None}

# ---------- API View ----------
@method_decorator(csrf_exempt, name='dispatch')
class SEOByCoordsView(APIView):
    def post(self, request, *args, **kwargs):
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        target_url = request.data.get('url')

        if not lat or not lon or not target_url:
            return Response(
                {'error': 'latitude, longitude, and url are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 1: Reverse geocode using Nominatim
        place = coords_to_place(lat, lon)
        city = place.get('city') or "Unknown"
        region = place.get('region') or "Unknown"
        country = place.get('country') or "Unknown"

        # Step 2: Call SerpApi to get live SEO data
        query = f"site:{target_url} SEO {city}"
        serp_url = f"https://serpapi.com/search.json?q={query}&location={city},{region},{country}&api_key={SERP_API_KEY}"

        try:
            resp = requests.get(serp_url, timeout=10)
            resp.raise_for_status()
            serp_data = resp.json()
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch SEO data: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Step 3: Extract organic results
        organic_results = serp_data.get('organic_results', [])
        seo_results = []
        for idx, r in enumerate(organic_results, start=1):
            snippet = r.get('snippet', '')
            seo_results.append({
                'ranking': idx,
                'title': r.get('title'),
                'link': r.get('link'),
                'snippet': snippet,
                'content_length': len(snippet),
                'keyword': target_url
            })

        # Step 4: Return results
        return Response({
            'resolved_place': {'city': city, 'region': region, 'country': country},
            'seo_results': seo_results
        }, status=status.HTTP_200_OK)

# ---------- Serve Frontend ----------
def index(request):
    return render(request, 'index.html')
