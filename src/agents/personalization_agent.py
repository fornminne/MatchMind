"""Personalization agent: reshape output per persona."""


class PersonalizationAgent:
    def view(self, narrative, persona="casual", favorite_team=None, favorite_player=None):
        if persona == "analyst":
            return {"detail": "high", "text": narrative}
        if favorite_team:
            return {"detail": "team_focus", "team": favorite_team, "text": narrative}
        if favorite_player:
            return {"detail": "player_focus", "player": favorite_player, "text": narrative}
        return {"detail": "casual", "text": narrative}
