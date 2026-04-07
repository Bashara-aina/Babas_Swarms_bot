# Skill: Location-Aware Advisor

## When to use
When Bashara asks for place recommendations, local info, or travel help — especially
without specifying a location (because you already know where he lives).

## User's default location
- **Home**: Koto City, Tokyo, Japan
- **Timezone**: Asia/Tokyo (JST, UTC+9)
- **Language context**: Indonesian or English, Japanese places but English/Indonesian queries

## What this skill enables
- Restaurant / cafe / ramen / sushi recommendations near home or a specified area
- Hotel and itinerary recommendations for trips
- Local event discovery ("what's happening in Tokyo this weekend?")
- Transport directions ("how do I get from Koto City to Shinjuku?")
- Travel planning: combine location + budget + preferences

## How to use LocationAdvisor

```python
from tools.location_advisor import LocationAdvisor
from core.memory.user_profile import UserProfile

profile = UserProfile()
location = profile.get("location", "Tokyo, Japan")
advisor = LocationAdvisor()

# Restaurant recommendation
result = await advisor.recommend_places("good ramen near home", location)

# Travel planning
result = await advisor.travel_advisor("Osaka", location)

# General local info
result = await advisor.get_local_info("events this weekend", location)
```

## Behaviour rules
- Always pull location from UserProfile first — don't ask Bashara where he is unless
  it's a different destination
- For travel questions, distinguish between "near home" (use stored location) and
  "trip to X" (use destination as target)
- Combine web search results with your knowledge for best accuracy
- Be specific: give place names, neighbourhoods, price ranges if available
- Don't make up addresses or ratings — if data is thin, say so and suggest how to search

## Example queries this handles
- "rekomendasiin restoran enak dekat rumah"
- "where should I eat in Tokyo today?"
- "plan a weekend trip to Kyoto"
- "best ramen near Koto City"
- "hotel murah di Osaka bulan depan"
- "how do I get to Akihabara from home?"
