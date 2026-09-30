"""
app.py
======
AquaGuard AI - Intelligent Watershed Priority Mapping & Decision Support System
Flask Application Entrypoint
Runs fully offline with OpenStreetMap tiles and self-contained static assets.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_file, Response
import io

from scoring_engine import (
    calculate_water_stress,
    generate_recommendations,
    simulate_interventions,
    WEIGHTS
)
from reports import generate_watershed_pdf, generate_watersheds_csv

app = Flask(__name__, static_folder='static', template_folder='templates')

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'watersheds.json')


def load_watersheds():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_scored_watersheds(custom_overrides_dict=None):
    """
    Returns watersheds augmented with computed scores, contributions, and priority.
    """
    watersheds = load_watersheds()
    results = []
    for w in watersheds:
        wid = w['id']
        overrides = custom_overrides_dict.get(wid) if custom_overrides_dict else None
        score_info = calculate_water_stress(w, overrides)
        item = dict(w)
        if overrides:
            item.update(overrides)
        item['score_data'] = score_info
        item['score'] = score_info['composite_score']
        item['priority'] = score_info['priority']
        item['priority_level'] = score_info['priority_level']
        item['badge_color'] = score_info['badge_color']
        results.append(item)
    # Sort high priority first
    results.sort(key=lambda x: x['score'], reverse=True)
    return results


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/watersheds', methods=['GET'])
def api_get_watersheds():
    """
    Returns all micro-watersheds with baseline calculations.
    """
    scored = get_all_scored_watersheds()
    return jsonify({
        'status': 'success',
        'count': len(scored),
        'watersheds': scored,
        'weights': WEIGHTS
    })


@app.route('/api/watershed/<wid>', methods=['GET'])
def api_get_watershed_detail(wid):
    """
    Fetches detailed calculations, parameter breakdown, and recommendations for a single watershed.
    """
    watersheds = load_watersheds()
    target = next((w for w in watersheds if w['id'] == wid), None)
    if not target:
        return jsonify({'status': 'error', 'message': 'Watershed not found'}), 404

    score_data = calculate_water_stress(target)
    recommendations = generate_recommendations(target, score_data)

    return jsonify({
        'status': 'success',
        'watershed': target,
        'score_data': score_data,
        'recommendations': recommendations
    })


@app.route('/api/simulate-interventions', methods=['POST'])
def api_simulate_interventions():
    """
    Runs Intervention Impact Simulator:
    Computes current score, predicted score, % risk reduction, estimated recharge, and combo.
    """
    req_data = request.get_json() or {}
    wid = req_data.get('watershed_id')
    selected = req_data.get('interventions', [])
    rain_drop_pct = float(req_data.get('rainfall_drop_pct', 0))

    watersheds = load_watersheds()
    target = next((w for w in watersheds if w['id'] == wid), None)
    if not target:
        return jsonify({'status': 'error', 'message': 'Watershed not found'}), 404

    # Base score
    score_data = calculate_water_stress(target)
    
    # Run impact simulation
    sim_result = simulate_interventions(
        score_data,
        selected,
        custom_modifiers={'rainfall_drop_pct': rain_drop_pct}
    )

    # Recalculate tailored recommendations under simulation
    recs = generate_recommendations(target, score_data)

    return jsonify({
        'status': 'success',
        'watershed': target,
        'simulation': sim_result,
        'recommendations': recs
    })


@app.route('/api/simulate-risk-scenario', methods=['POST'])
def api_simulate_risk_scenario():
    """
    Water Risk Simulator: applies global or watershed-specific climate stress
    such as rainfall drop, vegetation drought loss, or slope factor changes across all watersheds.
    """
    req_data = request.get_json() or {}
    rainfall_change_pct = float(req_data.get('rainfall_change_pct', 0.0))  # e.g. -20%
    ndvi_change_pct = float(req_data.get('ndvi_change_pct', 0.0))          # e.g. -15%
    selected_wid = req_data.get('watershed_id', None)

    watersheds = load_watersheds()
    results = []

    for w in watersheds:
        # Check if global or single
        if selected_wid and w['id'] != selected_wid:
            s_info = calculate_water_stress(w)
            item = dict(w)
            item['score_data'] = s_info
            item['score'] = s_info['composite_score']
            item['priority'] = s_info['priority']
            item['badge_color'] = s_info['badge_color']
            item['delta'] = 0.0
            results.append(item)
            continue

        orig_rain = float(w.get('rainfall_mm', 600))
        orig_ndvi = float(w.get('ndvi', 0.3))

        new_rain = max(150.0, orig_rain * (1.0 + (rainfall_change_pct / 100.0)))
        new_ndvi = max(0.04, min(0.95, orig_ndvi * (1.0 + (ndvi_change_pct / 100.0))))

        sim_overrides = {
            'rainfall_mm': round(new_rain, 1),
            'ndvi': round(new_ndvi, 2)
        }

        orig_score = calculate_water_stress(w)['composite_score']
        sim_score_info = calculate_water_stress(w, sim_overrides)
        sim_score = sim_score_info['composite_score']

        item = dict(w)
        item.update(sim_overrides)
        item['score_data'] = sim_score_info
        item['score'] = sim_score
        item['priority'] = sim_score_info['priority']
        item['badge_color'] = sim_score_info['badge_color']
        item['delta'] = round(sim_score - orig_score, 2)
        results.append(item)

    results.sort(key=lambda x: x['score'], reverse=True)

    return jsonify({
        'status': 'success',
        'rainfall_change_pct': rainfall_change_pct,
        'ndvi_change_pct': ndvi_change_pct,
        'watersheds': results
    })


@app.route('/api/export/pdf', methods=['GET'])
def export_pdf():
    """
    Downloads executive diagnostic PDF report for selected watershed.
    """
    wid = request.args.get('id', 'MW-IND-01')
    watersheds = load_watersheds()
    target = next((w for w in watersheds if w['id'] == wid), None)
    if not target:
        return "Watershed not found", 404

    score_data = calculate_water_stress(target)
    recommendations = generate_recommendations(target, score_data)

    # Optional simulation params
    interventions = request.args.get('interventions', '').split(',')
    interventions = [i.strip() for i in interventions if i.strip()]
    rain_drop = float(request.args.get('rainfall_drop_pct', 0))

    sim_data = None
    if interventions or rain_drop != 0:
        sim_data = simulate_interventions(score_data, interventions, {'rainfall_drop_pct': rain_drop})

    pdf_bytes = generate_watershed_pdf(target, score_data, recommendations, sim_data)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"AquaGuard_Report_{wid}.pdf"
    )


@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """
    Downloads prioritized micro-watershed assessment CSV report.
    """
    watersheds = load_watersheds()
    scores_dict = {}
    for w in watersheds:
        scores_dict[w['id']] = calculate_water_stress(w)

    csv_data = generate_watersheds_csv(watersheds, scores_dict)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=AquaGuard_Watershed_Rankings.csv"}
    )


if __name__ == '__main__':
    print("=" * 70)
    print(" AQUAGUARD AI - Intelligent Watershed Priority Mapping & Decision Support ")
    print(" Initializing standalone offline server at http://127.0.0.1:5000 ")
    print(" All systems operational with 22 Indian Micro-Watersheds ")
    print("=" * 70)
    app.run(host='127.0.0.1', port=5000, debug=True)
