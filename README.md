# BU SoundScape

**An interactive noise map of Bennett University, compared against World Health Organization limits.**

BU SoundScape is an Environmental Studies (EVS) project that maps how loud each part of the campus is at five times of the day, shows where it breaks WHO guidelines, and points students to the quietest places to study.

It has two parts that work together:

- **`noise_map.html`**: an interactive satellite map with a time-of-day selector and a smooth noise surface.
- **`index.html`**: the project website. It embeds the map and builds all of its charts directly from the data.

> **Live site:** https://busoundscape.netlify.app

---

## Features

### Map

- Noise surface drawn from the readings, colored by actual decibel level, over a satellite base map
- Five time slots: Morning, Afternoon, Evening, Night, Midnight, plus a play button that steps through the day
- Tap anywhere near a measured spot to see its dB level, how far it is above or below the WHO limit, the zone average, and all five time slots at a glance
- Zone outlines from the campus GeoJSON, with hover details
- The view is locked to the campus, so you cannot zoom out or pan far away from it
- Dark translucent interface; street, satellite and labelled-satellite layers available from the layer menu

### Website

- Hero with a mouse tracking effect using scrub.
- Embedded interactive map
- **WHO comparison:** campus average per time slot against the limit, and how far each zone sits above or below it
- **Analytics:** zone by time heat grid, and a line chart of how each type of zone changes through the day
- **Impact on students:** sleep, focus, stress, results, hearing and community
- **Solutions:** tick-lists for what students and the campus can do, with a progress ring
- **Top 3 places to focus:** ranked from the data, and re-ranked for any time slot you choose
- "Hear the difference" sound demo, scroll animations and hover effects

**None of the numbers or charts are hard coded.** The website reads the CSV and calculates everything in the browser, so updating the data and rebuilding updates every figure, chart and ranking.

---

## Project structure

```
BU-SoundScape/
├── index.html                          # Built website 
├── noise_map.html                      # Built interactive map 
├── site_template.html                  # Website design, text and code 
├── build_site.py                       # Builds index.html from the template + data
├── build_noise_map.py                  # Builds noise_map.html from the data + GeoJSON
├── NoiseDataAvg.csv                    # Average noise per location per time slot 
├── NoiseDataMain.csv                   # Individual readings: date, time, location, dB
├── zones.geojson                       # Campus zone polygons and categories
└── zones_with_centers_and_vertices.csv # Zone centers and vertices
```

---

## The data

**`NoiseDataMain.csv`** holds every individual reading.

| Column                  | Meaning                                                            |
| ----------------------- | ------------------------------------------------------------------ |
| `date`, `day`           | Date of the reading and weekday                                    |
| `zone`, `point_id`      | Campus zone and the fixed reference point within it                |
| `time_slot`, `time`     | Morning, Afternoon, Evening, Night or Midnight, and the clock time |
| `latitude`, `longitude` | Location of the reading                                            |
| `decibels`              | Noise level in dB                                                  |

Blank rows are visits that were missed.

**`NoiseDataAvg.csv`** is the averaged version that the map and website use.

| Column                  | Meaning                                |
| ----------------------- | -------------------------------------- |
| `zone`, `point_id`      | Zone and reference point               |
| `time_slot`             | Time of day                            |
| `latitude`, `longitude` | Location of the reference point        |
| `decibels`              | Average level over the study period    |
| `readings`              | Number of readings behind that average |

> **Note on the data:** Field readings were recorded with the NoiseTracker app (NEERI and CSIR). Coverage of the campus and the time slots was extended using interpolation.

---

## How the numbers are read

- **WHO limits used:** 55 dB outdoors in the daytime (Morning, Afternoon, Evening) and 45 dB at night (Night, Midnight), from the WHO Guidelines for Community Noise. 50 dB marks moderate annoyance.
- **Map colors:** blue to green to yellow to orange to red, running from 38 to 78 dB. Green is about the WHO night limit, yellow is about the WHO daytime limit, and orange and red are clearly above them.
- **Noise surface:** each point on the map is colored from nearby readings using inverse-distance weighting, and fades out away from measured spots.

---

## Limitations

- Measurements come from a limited number of fixed reference points, and the surface between them is an interpolation.
- The map uses Google's tile server without an official licence, which is fine for a college project but not for a commercial site.
- The WHO values are guideline limits for community noise, not legal limits.

---

## Acknowledgements

- NoiseTracker app by NEERI and CSIR for field recording
- World Health Organization, Guidelines for Community Noise
- [Leaflet](https://leafletjs.com/) and [folium](https://python-visualization.github.io/folium/) for mapping

## License

- This project is solely for academic purposes.
