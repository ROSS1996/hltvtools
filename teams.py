from bs4 import BeautifulSoup
import re
import requests
import json

all_teams = {
    "teams": []
}


def main():
    with open('teamlist.txt') as f:
        teamList = [line.rstrip().split(",") for line in f]

    for team in teamList:
        scrape(team[1], team[0])

    save_to_json()


def scrape(team_id, team_name):
    url = f"https://www.hltv.org/team/{team_id}/{team_name}"

    try:
        html = get_html(url)
        team_data = parse_team_data(html, team_id)
        save_team(team_data, team_name)
    except Exception as e:
        print(f"An error occurred: {e}")


def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return response.text


def parse_team_data(baseHtml, team_id):
    soup = BeautifulSoup(baseHtml, 'html.parser')
    team_profile = soup.select_one('.teamProfile')

    if not team_profile:
        raise ValueError(
            f"Team {team_id} not found. Either the name or id is wrong")

    lineup = team_profile.select('.bodyshot-team > *')

    name_element = team_profile.select_one('.profile-team-name')
    if not name_element:
        raise ValueError(f"Name for team {team_id} not found")
    name = name_element.text

    logo_element = team_profile.select_one('.teamlogo')
    if not logo_element:
        raise ValueError(f"Logo for team {team_id} not found")
    logo = logo_element['src']

    stats_container = team_profile.select('.profile-team-stats-container > *')
    ranking_element = stats_container[0].select_one('.right')
    if not ranking_element:
        raise ValueError(f"Ranking for team {team_id} not found")
    ranking = to_int(ranking_element.text.replace('#', ''))

    coach_container = soup.select_one('.teamCoach-wrapper')
    if coach_container:
        img_element = coach_container.select_one('.playerBox-bodyshot')
        if not img_element:
            img_element = coach_container.select_one('.playerBox-squareshot')
        if not img_element:
            raise ValueError(f"Coach for team {team_id} not found")
        coach = {
            'name': img_element['title'],
            'image': img_element['src'] if img_element['src'].startswith('http') else "https://www.hltv.org" + img_element['src']
        }
    else:
        coach = {'name': '', 'image': ''}

    players_container = soup.select_one('.playersBox-wrapper > table > tbody')
    if not players_container:
        raise ValueError(f"Players not found. Either the name or id is wrong")

    players = []
    bench = []
    for player in players_container.select('tr'):
        info = player.select_one('.playersBox-first-cell')
        if not info:
            raise ValueError(
                f"Player info not found for a player in team {team_id}")
        player_link = info.select_one('a')
        if not player_link:
            raise ValueError(
                f"Player link not found for a player in team {team_id}")
        player_link_href = player_link["href"]
        player_id, player_link_name = player_link_href.split("/")[-2:]
        nickname_element = player.select_one('.playersBox-playernick > div')
        if not nickname_element:
            raise ValueError(
                f"Nickname not found for a player in team {team_id}")
        nickname = nickname_element.text
        status_element = player.select_one('.player-status')
        if not status_element:
            raise ValueError(
                f"Status not found for a player in team {team_id}")
        status = status_element.text.capitalize()
        if status != 'Starter':
            bench.append({
                "nickname": nickname,
                "playerId": to_int(player_id),
                "playerLinkName": player_link_name,
                "status": status
            })
        else:
            players.append({
                "nickname": nickname,
                "playerId": to_int(player_id),
                "playerLinkName": player_link_name,
                "status": status
            })

    return {
        "id": to_int(team_id),
        "name": name,
        "logo": logo,
        "ranking": to_int(ranking),
        "coach": coach,
        "players": players,
        "bench": bench
    }


def save_team(team_data, team_name):
    all_teams['teams'].append(team_data)
    print(f"{team_name} saved")


def save_to_json():
    file_name = f"teams.json"
    # Write the team data to the file
    with open(file_name, 'w') as f:
        json.dump(all_teams, f, indent=4)

    print(f"Scrap job finished")


def to_float(value):
    try:
        return float(value)
    except ValueError:
        return 0.00


def to_int(value):
    try:
        return int(value)
    except ValueError:
        return 0


if __name__ == '__main__':
    main()
