import argparse
import json
from agent import run_agent

def main():
    parser = argparse.ArgumentParser(description="Flash Flood Street Ranker CLI")
    parser.add_argument("--location", type=str, default="Chavakkad", help="Location name (Default: Chavakkad)")
    parser.add_argument("--lat", type=float, default=10.53, help="Latitude (Default: Chavakkad = 10.53)")
    parser.add_argument("--lon", type=float, default=76.02, help="Longitude (Default: Chavakkad = 76.02)")
    
    args = parser.parse_args()
    
    print(f"Triggering Flood Ranker Agent for {args.location}...")
    result = run_agent(args.location, args.lat, args.lon)
    
    if result.get("errors"):
        print("\nErrors encountered:")
        for error in result.get("errors"):
            print(f"- {error}")
    
    print("\n[Weather Data]")
    print(json.dumps(result.get("weather", {}), indent=2))
    
    print("\n[Ranked Streets for Evacuation Priority]")
    rankings = result.get("rankings", [])
    if not rankings:
        print("No rankings were generated due to an error.")
    else:
        for idx, r in enumerate(rankings):
            print(f"{idx+1}. {r.get('street_name')} (Score: {r.get('vulnerability_score')}/100)")
            print(f"   Reason: {r.get('reason')}")

if __name__ == "__main__":
    main()
