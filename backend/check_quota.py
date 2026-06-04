"""Check Gemini API quota and rate limits."""
import sys
sys.path.insert(0, r'c:\Users\Fab2\Desktop\AI\_plasticFlower\backend')

from app.config import get_settings
import google.generativeai as genai
from datetime import datetime

try:
    s = get_settings()
    api_key = s.gemini_api_key.get_secret_value()
    genai.configure(api_key=api_key)
    
    print("\n" + "="*80)
    print("GEMINI API RATE LIMITS")
    print("="*80 + "\n")
    
    print("NOTE: Google does NOT expose rate limits through the API.")
    print("The limits below are from official documentation as of December 2024.")
    print("Check the official docs for the most current information.")
    print("\nOfficial Documentation:")
    print("https://ai.google.dev/pricing")
    print("="*80 + "\n")
    # Display documented rate limits (from official documentation)
    # Source: https://ai.google.dev/pricing
    
    rate_limits = {
        "Gemini 2.5 Flash": {
            "Free Tier": "15 RPM, 1,500 RPD, 1M TPM",
            "Pay-as-you-go": "2,000 RPM, 4M TPM"
        },
        "Gemini 2.5 Pro": {
            "Free Tier": "2 RPM, 50 RPD",
            "Pay-as-you-go": "1,000 RPM, 4M TPM"
        },
        "Gemini 2.0 Flash Experimental": {
            "Free Tier": "10 RPM, 1,500 RPD",
            "Pay-as-you-go": "N/A (experimental)"
        },
        "Gemini 2.0 Flash": {
            "Free Tier": "15 RPM, 1,500 RPD, 1M TPM",
            "Pay-as-you-go": "2,000 RPM, 4M TPM"
        },
        "Gemini 1.5 Flash": {
            "Free Tier": "15 RPM, 1,500 RPD, 1M TPM",
            "Pay-as-you-go": "2,000 RPM, 4M TPM"
        },
        "Gemini 1.5 Pro": {
            "Free Tier": "2 RPM, 50 RPD",
            "Pay-as-you-go": "1,000 RPM, 4M TPM"
        },
        "Gemma Models": {
            "Free Tier": "15 RPM, 1,500 RPD",
            "Pay-as-you-go": "Check documentation"
        },
        "Embedding Models": {
            "Free Tier": "1,500 RPD",
            "Pay-as-you-go": "1,500 RPM"
        }
    }
    
    print("FREE TIER RATE LIMITS (per minute/day):")
    print("="*80)
    print("\nLegend: RPM = Requests Per Minute, RPD = Requests Per Day, TPM = Tokens Per Minute\n")
    
    for model_family, limits in rate_limits.items():
        print(f"\n{model_family}:")
        print("-" * 80)
        print(f"  Free Tier: {limits['Free Tier']}")
        print(f"  Pay-as-you-go: {limits['Pay-as-you-go']}")
    
    print("\n" + "="*80)
    print("\nIMPORTANT NOTES:")
    print("-" * 80)
    print("1. Rate limits are PER API KEY")
    print("2. Limits reset at the start of each calendar day (Pacific Time)")
    print("3. Going over limits results in HTTP 429 (Too Many Requests) errors")
    print("4. Consider upgrading to pay-as-you-go for higher limits")
    print("5. These limits are subject to change - check official docs")
    
    # Test API connection
    print("\n" + "="*80)
    print("TESTING API CONNECTION...")
    print("-" * 80)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            "Respond with just 'OK'",
            generation_config=genai.GenerationConfig(
                max_output_tokens=5,
                temperature=0
            )
        )
        print(f"\nAPI Test: SUCCESS")
        print(f"Response: {response.text.strip()}")
        print(f"Status: Your API key is working")
        
    except Exception as e:
        print(f"\nAPI Test: FAILED")
        print(f"Error: {e}")
    
    print("\n" + "="*80)
    print("QUOTA MONITORING OPTIONS:")
    print("-" * 80)
    print("1. Google AI Studio: https://aistudio.google.com/app/apikey")
    print("   - View API keys and basic usage")
    print("\n2. Google Cloud Console: https://console.cloud.google.com/")
    print("   - Navigate to: APIs & Services > Enabled APIs > Gemini API")
    print("   - View detailed quotas and usage metrics")
    print("\n3. Enable Cloud Monitoring for detailed usage tracking")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\nERROR: {e}")
    print("\nMake sure:")
    print("  1. Your .env file has GEMINI_API_KEY set")
    print("  2. The API key is valid")
    print("  3. You have internet connection")
    sys.exit(1)
