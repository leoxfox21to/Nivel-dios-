def apply_filters(game_data: dict) -> dict:
    """
    Aplica filtros al partido antes de enviarlo a Groq.
    Devuelve {'skip': bool, 'warnings': list}.
    """
    warnings = []
    skip = False

    # Regla 1: Historial insuficiente — solo advertencia, no bloquea
    # (en playoffs BallDontLie no devuelve datos históricos)
    home_games = len(game_data["home_last_10"])
    away_games = len(game_data["away_last_10"])
    if home_games == 0 and away_games == 0:
        warnings.append("⚠️ Sin historial reciente — análisis basado solo en cuotas de mercado")
    elif home_games < 10 or away_games < 10:
        warnings.append(f"⚠️ Historial parcial ({home_games}/{away_games} partidos) — confianza reducida")

    # Regla 2: Estrella lesionada (20+ PPG)
    stars_out = [
        p for p in game_data["home_injuries"] + game_data["away_injuries"]
        if p.get("avg_points", 0) >= 20
    ]
    for player in stars_out:
        warnings.append(f"⚠️ Baja estrella: {player['name']} ({player['avg_points']} PPG)")

    if len(stars_out) >= 2:
        skip = True
        warnings.append("2+ estrellas lesionadas — pick no recomendada")

    # Regla 3: Visitante en back to back
    if game_data["away_is_back_to_back"]:
        warnings.append("⚠️ Visitante juega Back to Back — rendimiento reducido ~15%")

    # Regla 4: Sin línea de mercado — esto sí bloquea el análisis
    if not game_data["over_under_line"]:
        skip = True
        warnings.append("Sin línea de mercado disponible — no se puede analizar")

    return {"skip": skip, "warnings": warnings}
