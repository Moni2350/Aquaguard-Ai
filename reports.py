"""
reports.py
==========
Export engine for AquaGuard AI:
- Generates professional downloadable PDF report with reportlab
- Generates downloadable CSV report for any watershed or all watersheds
"""

import io
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_watershed_pdf(watershed, score_data, recommendations, simulation=None):
    """
    Builds a high-impact, professional executive PDF report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom modern styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0284c7')
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    body_bold = ParagraphStyle(
        'ReportBodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    elements = []

    # Header Banner
    elements.append(Paragraph("AQUAGUARD AI – WATERSHED DECISION SUPPORT REPORT", title_style))
    elements.append(Paragraph(f"Micro-Watershed Priority & Conservation Diagnostic | Generated System Report", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284c7'), spaceBefore=8, spaceAfter=14))

    # General Attributes Table
    elements.append(Paragraph("1. General Watershed Hydro-geological Profile", section_heading))
    profile_data = [
        [
            Paragraph("<b>Identifier:</b>", body_style), Paragraph(watershed.get('id', 'N/A'), body_bold),
            Paragraph("<b>Location:</b>", body_style), Paragraph(f"{watershed.get('district', '')}, {watershed.get('state', '')}", body_bold)
        ],
        [
            Paragraph("<b>Watershed Name:</b>", body_style), Paragraph(watershed.get('name', ''), body_bold),
            Paragraph("<b>Drainage Area:</b>", body_style), Paragraph(f"{watershed.get('area_sq_km', 0)} sq km", body_bold)
        ],
        [
            Paragraph("<b>Annual Rainfall:</b>", body_style), Paragraph(f"{watershed.get('rainfall_mm', 0)} mm/year", body_bold),
            Paragraph("<b>Mean Slope:</b>", body_style), Paragraph(f"{watershed.get('slope_deg', 0)}°", body_bold)
        ],
        [
            Paragraph("<b>Dominant Soil:</b>", body_style), Paragraph(str(watershed.get('soil_type', '')), body_bold),
            Paragraph("<b>Drainage Density:</b>", body_style), Paragraph(f"{watershed.get('drainage_density_km_per_sq_km', 0)} km/km²", body_bold)
        ],
        [
            Paragraph("<b>Vegetation (NDVI):</b>", body_style), Paragraph(f"{watershed.get('ndvi', 0)}", body_bold),
            Paragraph("<b>Surface Water:</b>", body_style), Paragraph(f"{watershed.get('surface_water_pct', 0)}% area", body_bold)
        ],
        [
            Paragraph("<b>Land Use Class:</b>", body_style), Paragraph(str(watershed.get('land_use', '')), body_bold),
            Paragraph("<b>Beneficiary Pop:</b>", body_style), Paragraph(f"{watershed.get('population', 0):,}", body_bold)
        ]
    ]

    t_profile = Table(profile_data, colWidths=[110, 160, 110, 160])
    t_profile.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_profile)

    # Score & Priority Summary
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("2. Composite Water Stress Assessment & Formula Breakdown", section_heading))
    
    score = score_data['composite_score']
    priority = score_data['priority']
    
    score_summary = [
        [
            Paragraph("<b>Composite Water Stress Score:</b>", body_bold),
            Paragraph(f"<font size=14 color='#0284c7'><b>{score} / 10.0</b></font>", body_bold),
            Paragraph("<b>Priority Level:</b>", body_bold),
            Paragraph(f"<b>{priority}</b>", body_bold)
        ]
    ]
    t_score = Table(score_summary, colWidths=[170, 100, 100, 170])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e0f2fe')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#38bdf8')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_score)
    elements.append(Spacer(1, 6))

    # Formula Display
    elements.append(Paragraph(f"<b>Formula:</b> <font color='#64748b'>{score_data['formula_text']}</font>", body_style))
    elements.append(Spacer(1, 6))

    # Parameter Breakdown Table
    breakdown_headers = [
        Paragraph("<b>Parameter</b>", body_bold),
        Paragraph("<b>Weight</b>", body_bold),
        Paragraph("<b>Raw Value</b>", body_bold),
        Paragraph("<b>Normalized (1-10)</b>", body_bold),
        Paragraph("<b>Weighted Val</b>", body_bold),
        Paragraph("<b>Contribution %</b>", body_bold)
    ]
    breakdown_rows = [breakdown_headers]
    
    param_meta = [
        ("Rainfall Deficit", "25%", f"{watershed.get('rainfall_mm')} mm", score_data['normalized']['rainfall'], score_data['weighted_values']['rainfall'], f"{score_data['contributions_pct']['rainfall']}%"),
        ("NDVI / Vegetation", "20%", f"{watershed.get('ndvi')}", score_data['normalized']['ndvi'], score_data['weighted_values']['ndvi'], f"{score_data['contributions_pct']['ndvi']}%"),
        ("Slope / Relief", "15%", f"{watershed.get('slope_deg')}°", score_data['normalized']['slope'], score_data['weighted_values']['slope'], f"{score_data['contributions_pct']['slope']}%"),
        ("Soil Texture Vulnerability", "15%", f"{watershed.get('soil_type')}", score_data['normalized']['soil'], score_data['weighted_values']['soil'], f"{score_data['contributions_pct']['soil']}%"),
        ("Drainage Density", "10%", f"{watershed.get('drainage_density_km_per_sq_km')} km/km²", score_data['normalized']['drainage_density'], score_data['weighted_values']['drainage_density'], f"{score_data['contributions_pct']['drainage_density']}%"),
        ("Surface Water Deficit", "10%", f"{watershed.get('surface_water_pct')}%", score_data['normalized']['surface_water'], score_data['weighted_values']['surface_water'], f"{score_data['contributions_pct']['surface_water']}%"),
        ("Land Use Vulnerability", "5%", f"{watershed.get('land_use')}", score_data['normalized']['land_use'], score_data['weighted_values']['land_use'], f"{score_data['contributions_pct']['land_use']}%")
    ]
    
    for row in param_meta:
        breakdown_rows.append([
            Paragraph(row[0], body_style),
            Paragraph(row[1], body_style),
            Paragraph(row[2], body_style),
            Paragraph(str(row[3]), body_style),
            Paragraph(str(row[4]), body_style),
            Paragraph(f"<b>{row[5]}</b>", body_style)
        ])

    t_breakdown = Table(breakdown_rows, colWidths=[130, 60, 110, 80, 80, 80])
    t_breakdown.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_breakdown)

    # Recommendations Section
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("3. Recommended Engineering & Conservation Interventions", section_heading))
    
    rec_headers = [
        Paragraph("<b>Intervention Type</b>", body_bold),
        Paragraph("<b>Scope & Scale</b>", body_bold),
        Paragraph("<b>Est. Recharge</b>", body_bold),
        Paragraph("<b>Impact Rationale</b>", body_bold)
    ]
    rec_rows = [rec_headers]
    for r in recommendations:
        rec_rows.append([
            Paragraph(f"<b>{r['name']}</b>", body_style),
            Paragraph(r['units'], body_style),
            Paragraph(f"+{r['est_recharge_gain_mcm']} MCM", body_bold),
            Paragraph(r['rationale'], body_style)
        ])

    t_recs = Table(rec_rows, colWidths=[120, 120, 80, 220])
    t_recs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_recs)

    # Simulation Section (if present)
    if simulation:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("4. Scenario Simulation & Predicted Mitigation Results", section_heading))
        sim_data = [
            [
                Paragraph("<b>Baseline Stress Score:</b>", body_style), Paragraph(str(simulation.get('current_score')), body_bold),
                Paragraph("<b>Predicted Future Score:</b>", body_style), Paragraph(f"<font color='#0284c7'><b>{simulation.get('predicted_score')}</b></font>", body_bold)
            ],
            [
                Paragraph("<b>Risk Reduction Achieved:</b>", body_style), Paragraph(f"<font color='#16a34a'><b>-{simulation.get('risk_reduction_pct')}%</b></font>", body_bold),
                Paragraph("<b>Est. Cumulative Recharge:</b>", body_style), Paragraph(f"<b>+{simulation.get('estimated_recharge_gain_mcm')} MCM</b>", body_bold)
            ],
            [
                Paragraph("<b>Projected Priority Tier:</b>", body_style), Paragraph(f"<b>{simulation.get('predicted_priority')}</b>", body_bold),
                Paragraph("<b>Active Interventions:</b>", body_style), Paragraph(", ".join(simulation.get('active_interventions', [])), body_style)
            ]
        ]
        t_sim = Table(sim_data, colWidths=[130, 140, 130, 140])
        t_sim.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#86efac')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbf7d0')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_sim)

    # Footer notice
    elements.append(Spacer(1, 14))
    elements.append(Paragraph("<i>AquaGuard AI Decision Support System — Developed for National Hydrological & Water Conservation Hackathon. Generated with zero external API dependencies.</i>", subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_watersheds_csv(watersheds_list, scores_dict):
    """
    Builds a CSV containing ranked micro-watershed assessment data.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Priority Rank", "Watershed ID", "Watershed Name", "District", "State",
        "Water Stress Score (1-10)", "Priority Level",
        "Rainfall (mm)", "NDVI", "Slope (deg)", "Soil Type",
        "Drainage Density (km/sq km)", "Surface Water (%)", "Land Use",
        "Drainage Area (sq km)", "Population",
        "Rainfall Contrib %", "NDVI Contrib %", "Slope Contrib %",
        "Soil Contrib %", "DD Contrib %", "SW Contrib %", "LU Contrib %"
    ])

    # Sort watersheds by score descending
    sorted_ws = sorted(
        watersheds_list,
        key=lambda w: scores_dict.get(w['id'], {}).get('composite_score', 0),
        reverse=True
    )

    for rank, w in enumerate(sorted_ws, 1):
        s = scores_dict.get(w['id'], {})
        contrib = s.get('contributions_pct', {})
        writer.writerow([
            rank,
            w.get('id'),
            w.get('name'),
            w.get('district'),
            w.get('state'),
            s.get('composite_score', 0),
            s.get('priority', ''),
            w.get('rainfall_mm'),
            w.get('ndvi'),
            w.get('slope_deg'),
            w.get('soil_type'),
            w.get('drainage_density_km_per_sq_km'),
            w.get('surface_water_pct'),
            w.get('land_use'),
            w.get('area_sq_km'),
            w.get('population'),
            contrib.get('rainfall', 0),
            contrib.get('ndvi', 0),
            contrib.get('slope', 0),
            contrib.get('soil', 0),
            contrib.get('drainage_density', 0),
            contrib.get('surface_water', 0),
            contrib.get('land_use', 0)
        ])

    output.seek(0)
    return output.getvalue()
