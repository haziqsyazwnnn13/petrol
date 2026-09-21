# Petrol Trip Calculator — Streamlit

A small mobile-friendly petrol calculator for estimating fuel range and remaining petrol after a trip.

## Features

- Enter starting fuel as **litres** or **RM**.
- Set petrol price in RM/L.
- Use an estimated **10–12 km/L** efficiency range.
- See estimated total range immediately.
- Enter actual **KM used** after the trip.
- Calculate **petrol left**, **KM left**, and estimated **RM value left**.
- Includes a simple petrol-tank visual and responsive CSS for phone screens.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the Streamlit URL shown in the terminal. On a phone, use the network URL printed by Streamlit (for example, `http://<your-computer-ip>:8501`) while your phone is on the same Wi-Fi.

## Notes

The calculator uses a basic estimated efficiency of 10–12 km/L. Actual fuel consumption can differ because of traffic, speed, road gradient, tyre pressure, load, air-conditioning, and driving style.
