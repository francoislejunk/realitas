"""
Spatial Location Analyzer - Dynamic Location Dimension Detection

Uses LLM to analyze scene descriptions and determine appropriate
spatial dimensions, location type, and layout characteristics.
"""

import json
from typing import Tuple, Optional
from openrouter_config import create_role_client, OpenRouterConfig


class SpatialLocationAnalyzer:
    """
    Analyzes scene descriptions to determine spatial characteristics.
    
    Uses LLM to intelligently determine:
    - Location dimensions (width x height)
    - Location type (interior/exterior)
    - Suggested zones
    - Suggested obstacles
    """
    
    def __init__(self, llm_client=None):
        """Initialize with optional LLM client"""
        if llm_client is None:
            llm_client = OpenRouterConfig.create_client()
        self.llm_client = llm_client
    
    def analyze_location(self, scene_description: str, location_name: str) -> dict:
        """
        Analyze scene description to determine spatial characteristics.
        
        Args:
            scene_description: Full narrative scene description
            location_name: Name/label of the location
        
        Returns:
            dict with keys:
                - width: int (units)
                - height: int (units)
                - location_type: str ("interior" or "exterior")
                - suggested_zones: list of zone descriptions
                - suggested_obstacles: list of obstacle descriptions
        """
        
        prompt = f"""Analyze this scene description and determine appropriate spatial dimensions and characteristics.

MEASUREMENT SYSTEM:
- Use **units as meters**. Treat **1 unit = 1 meter**.
- Return integers.

SCENE DESCRIPTION:
{scene_description}

LOCATION NAME: {location_name}

Determine:
1. **Width** (in units): How wide is this space?
   - Small room/office: 10-20 units
   - Medium room/shop: 20-30 units
   - Large room/workshop: 35-60 units
   - Very large interior (stable, hall, warehouse, market hall, temple): 70-120 units
   - Street/outdoor: 80-120 units

2. **Height** (in units): How deep/long is this space?
   - Narrow corridor: 10-15 units
   - Standard room: 15-25 units
   - Large space: 30-50 units
   - Very large interior (stable, hall, warehouse, market hall, temple): 50-90 units
   - Long street: 20-30 units (streets are wide but not deep)

3. **Location Type**: "interior" or "exterior"
   - **Interior**: ANY enclosed space with walls and a roof
     * Examples: garage, warehouse, office, shop, diner, bar, house, apartment, factory
     * Key: Has ceiling/roof and walls = interior
   - **Exterior**: Open outdoor spaces WITHOUT roof
     * Examples: street, park, alley, parking lot, field, plaza
     * Key: Open to sky = exterior
   
   **CRITICAL CLASSIFICATION RULES:**
   - Garage = INTERIOR (has roof and walls)
   - Warehouse = INTERIOR (has roof and walls)
   - Diner = INTERIOR (has roof and walls)
   - Street = EXTERIOR (open to sky)
   - Parking lot = EXTERIOR (open to sky)

4. **Suggested Zones** (2-4 distinct areas within the space):
   - Name, description, approximate position
   - **For streets**: MUST include "Road" and "Sidewalk" zones
   - **For buildings**: Include functional areas (entrance, main area, back, etc.)

5. **Suggested Obstacles** (2-5 physical objects that block movement):
   - Name, type, approximate position, blocks_movement, blocks_line_of_sight
   - **IMPORTANT**: Specify if obstacle is a "perimeter" (surrounds the area) or "interior" (inside the area)
   - **Perimeter obstacles**: Fences, walls, barriers that surround the entire location
   - **Interior obstacles**: Furniture, vehicles, equipment inside the space
   - **For streets**: Include parked vehicles, street furniture (benches, phone booths, etc.)
   - **For buildings**: Include furniture, equipment, structural elements

Respond in JSON format:
```json
{{
    "width": <integer>,
    "height": <integer>,
    "location_type": "interior" or "exterior",
    "reasoning": "Brief explanation of why these dimensions",
    "suggested_zones": [
        {{
            "name": "Zone Name",
            "description": "What this area is",
            "position": "front/back/left/right/center"
        }}
    ],
    "suggested_obstacles": [
        {{
            "name": "Obstacle Name",
            "type": "furniture/vehicle/debris/natural/structure",
            "position": "front/back/left/right/center",
            "is_perimeter": true/false,
            "blocks_movement": true/false,
            "blocks_line_of_sight": true/false
        }}
    ]
}}
```

EXAMPLES:

**Small Office:**
```json
{{
    "width": 12,
    "height": 10,
    "location_type": "interior",
    "reasoning": "Small private office with desk and filing cabinet",
    "suggested_zones": [
        {{"name": "Desk Area", "description": "Main workspace", "position": "center"}},
        {{"name": "Filing Area", "description": "Storage cabinets", "position": "back"}}
    ],
    "suggested_obstacles": [
        {{"name": "Desk", "type": "furniture", "position": "center", "blocks_movement": true, "blocks_line_of_sight": false}},
        {{"name": "Filing Cabinet", "type": "furniture", "position": "back", "blocks_movement": true, "blocks_line_of_sight": false}}
    ]
}}
```

**Diner:**
```json
{{
    "width": 25,
    "height": 20,
    "location_type": "interior",
    "reasoning": "Medium-sized diner with booths, counter, and kitchen access",
    "suggested_zones": [
        {{"name": "Dining Area", "description": "Booths and tables", "position": "front"}},
        {{"name": "Counter", "description": "Bar seating", "position": "center"}},
        {{"name": "Kitchen Door", "description": "Staff area", "position": "back"}}
    ],
    "suggested_obstacles": [
        {{"name": "Counter", "type": "furniture", "position": "center", "blocks_movement": true, "blocks_line_of_sight": false}},
        {{"name": "Booth Seating", "type": "furniture", "position": "left", "blocks_movement": true, "blocks_line_of_sight": false}}
    ]
}}
```

**City Street:**
```json
{{
    "width": 100,
    "height": 20,
    "location_type": "exterior",
    "reasoning": "Long city street with sidewalks and parked cars",
    "suggested_zones": [
        {{"name": "North Sidewalk", "description": "Pedestrian walkway", "position": "back"}},
        {{"name": "Road", "description": "Two-lane street", "position": "center"}},
        {{"name": "South Sidewalk", "description": "Pedestrian walkway", "position": "front"}}
    ],
    "suggested_obstacles": [
        {{"name": "Parked Car 1", "type": "vehicle", "position": "left", "blocks_movement": true, "blocks_line_of_sight": true}},
        {{"name": "Parked Car 2", "type": "vehicle", "position": "center", "blocks_movement": true, "blocks_line_of_sight": true}},
        {{"name": "Parked Car 3", "type": "vehicle", "position": "right", "blocks_movement": true, "blocks_line_of_sight": true}}
    ]
}}
```

Now analyze the provided scene and respond with JSON only."""

        try:
            response = self.llm_client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            analysis = json.loads(response_text)
            
            # Validate and set defaults
            analysis.setdefault("width", 20)
            analysis.setdefault("height", 15)
            analysis.setdefault("location_type", "interior")
            analysis.setdefault("reasoning", "Default dimensions")
            analysis.setdefault("suggested_zones", [])
            analysis.setdefault("suggested_obstacles", [])
            
            # Clamp dimensions to reasonable ranges
            analysis["width"] = max(10, min(150, analysis["width"]))
            analysis["height"] = max(10, min(100, analysis["height"]))
            
            # POST-PROCESSING VALIDATION: Fix obvious misclassifications
            location_lower = location_name.lower()
            loc_type = analysis["location_type"].lower()
            
            # Buildings with roofs = ALWAYS interior
            interior_keywords = ['garage', 'warehouse', 'diner', 'restaurant', 'cafe', 
                                'bar', 'pub', 'office', 'shop', 'store', 'house', 
                                'apartment', 'building', 'factory', 'workshop']
            
            # Open spaces = ALWAYS exterior
            exterior_keywords = ['street', 'road', 'alley', 'park', 'parking lot', 
                                'plaza', 'field', 'yard', 'sidewalk']
            
            # Check for forced interior
            if any(keyword in location_lower for keyword in interior_keywords):
                if loc_type == "exterior":
                    print(f"[SPATIAL ANALYZER] Correcting misclassification: {location_name} should be INTERIOR")
                    analysis["location_type"] = "interior"
                    analysis["reasoning"] += " (corrected from exterior to interior)"
            
            # Check for forced exterior
            elif any(keyword in location_lower for keyword in exterior_keywords):
                if loc_type == "interior":
                    print(f"[SPATIAL ANALYZER] Correcting misclassification: {location_name} should be EXTERIOR")
                    analysis["location_type"] = "exterior"
                    analysis["reasoning"] += " (corrected from interior to exterior)"

            return analysis
            
        except Exception as e:
            print(f"[SPATIAL ANALYZER] Error analyzing location: {e}")
            # Return safe defaults
            return {
                "width": 20,
                "height": 15,
                "location_type": "interior",
                "reasoning": "Fallback to default dimensions due to analysis error",
                "suggested_zones": [],
                "suggested_obstacles": []
            }
    
    def get_dimensions_only(self, scene_description: str, location_name: str) -> Tuple[int, int, str]:
        """
        Quick method to get just dimensions and type.
        
        Returns:
            (width, height, location_type)
        """
        analysis = self.analyze_location(scene_description, location_name)
        return (
            analysis["width"],
            analysis["height"],
            analysis["location_type"]
        )


# === GLOBAL ACCESSOR ===

_analyzer: Optional[SpatialLocationAnalyzer] = None

def get_location_analyzer() -> SpatialLocationAnalyzer:
    """Get or create global location analyzer"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SpatialLocationAnalyzer()
    return _analyzer


# === CONVENIENCE FUNCTION ===

def analyze_scene_for_spatial(scene_description: str, location_name: str) -> dict:
    """
    Quick function to analyze scene and get spatial characteristics.
    
    Args:
        scene_description: Full narrative scene description
        location_name: Name/label of the location
    
    Returns:
        dict with width, height, location_type, zones, obstacles
    """
    analyzer = get_location_analyzer()
    return analyzer.analyze_location(scene_description, location_name)
