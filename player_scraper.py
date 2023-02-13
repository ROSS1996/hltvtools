from bs4 import BeautifulSoup
import re
import requests
import json


def main():
    player_id = input("Enter the player ID: ")
    player_name = input("Enter the player name: ")
    player_name = player_name.lower()
    player_name = re.sub(r'\W+', '', player_name)
    base_url = f"https://www.hltv.org/stats/players/{player_id}/{player_name}"
    individual_url = f"https://www.hltv.org/stats/players/individual/{player_id}/{player_name}"
    statsUrl = None
    individualUrl = None

    filter_data = input("Do you want to filter the data by date range? (y/n) ")
    if filter_data in ['y', 'yes']:
        start_date = input("Enter the start date (YYYY-MM-DD): ")
        end_date = input("Enter the end date (YYYY-MM-DD): ")
        while end_date <= start_date:
            print("End date must be later than start date. Please try again.")
            end_date = input("Enter the end date (YYYY-MM-DD): ")
        statsUrl = f"{base_url}?startDate={start_date}&endDate={end_date}"
        individualUrl = f"{individual_url}?startDate={start_date}&endDate={end_date}"
    else:
        statsUrl = base_url
        individualUrl = individual_url
    try:
        baseHtml = get_html(statsUrl)
        individualHtml = get_html(individualUrl)
        overall = parse_player_data(baseHtml, player_id)
        individual = parse_individual_data(individualHtml)
        player_data = merge_data(overall, individual)
        save_to_json(player_data, f"{player_name}.json")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return response.text


def parse_player_data(baseHtml, player_id):
    soup = BeautifulSoup(baseHtml, 'html.parser')

    # Find the main table containing the player data
    main_table = soup.select_one('.playerSummaryStatBox')

    # Check if the table exists, return None if it doesn't
    if not main_table:
        return None

    # Extract image src
    image_block = main_table.select_one('.summaryBodyshotContainer')
    image = image_block.select('img')[1]['src']
    if image == "/img/static/player/player_silhouette.png":
        image = "https://www.hltv.org/img/static/player/player_silhouette.png"

    # Extract main table content
    main_table_content = main_table.select_one('.summaryBreakdownContainer')

    # Extract nickname
    nickname = main_table_content.select_one('.summaryNickname').text.strip()

    # Extract name
    name = main_table_content.select_one('.summaryRealname').text.strip()

    # Extract team name and id
    team_name = main_table_content.select_one('.SummaryTeamname').text.strip()
    team_link = main_table_content.select_one('.SummaryTeamname a')
    if team_link:
        team_id = int(team_link['href'].split('/')[3])
    else:
        team_id = None

    # Extract first row of stats
    stat_row_1 = main_table_content.select('.summaryStatBreakdownRow')[0]
    stat_breakdowns = stat_row_1.select('.summaryStatBreakdown')
    rating = to_float(stat_breakdowns[0].select_one(
        '.summaryStatBreakdownDataValue').text)
    dpr = to_float(stat_breakdowns[1].select_one(
        '.summaryStatBreakdownDataValue').text)
    kast = to_float(stat_breakdowns[2].select_one(
        '.summaryStatBreakdownDataValue').text.strip("%"))

    # Extract second row of stats
    stat_row_2 = main_table_content.select('.summaryStatBreakdownRow')[1]
    stat_breakdowns = stat_row_2.select('.summaryStatBreakdown')
    impact = to_float(stat_breakdowns[0].select_one(
        '.summaryStatBreakdownDataValue').text)
    adr = to_float(stat_breakdowns[1].select_one(
        '.summaryStatBreakdownDataValue').text)
    kpr = to_float(stat_breakdowns[2].select_one(
        '.summaryStatBreakdownDataValue').text)

    # Extract additional stats
    additional_stats = soup.select('.statistics .columns .col')
    headshots = to_float(additional_stats[0].select(
        '.stats-row')[1].select('span')[1].text.strip("%"))
    kdratio = to_float(additional_stats[0].select(
        '.stats-row')[3].select('span')[1].text)
    maps = to_int(additional_stats[0].select(
        '.stats-row')[6].select('span')[1].text.strip())
    rounds = to_int(additional_stats[1].select(
        '.stats-row')[0].select('span')[1].text.strip())
    assistsround = to_float(additional_stats[1].select(
        '.stats-row')[2].select('span')[1].text.strip())

    # Extract ratings
    rating_stats = soup.select('.rating-breakdown .rating-value')
    rt_top5 = to_float(rating_stats[0].text.strip())
    rt_top10 = to_float(rating_stats[1].text.strip())
    rt_top20 = to_float(rating_stats[2].text.strip())
    rt_top30 = to_float(rating_stats[3].text.strip())
    rt_top50 = to_float(rating_stats[4].text.strip())

    player_id = to_int(player_id)

    # Return the collected data as a dictionary
    return {
        'id': player_id,
        'image': image,
        'nickname': nickname,
        'name': name,
        'team': team_name,
        'team_id': team_id,
        'rating': rating,
        'dpr': dpr,
        'kast': kast,
        'impact': impact,
        'adr': adr,
        'kpr': kpr,
        'rounds': rounds,
        'headshots': headshots,
        'kdratio': kdratio,
        'assistsround': assistsround,
        'maps': maps,
        'ratingtop5': rt_top5,
        'ratingtop10': rt_top10,
        'ratingtop20': rt_top20,
        'ratingtop30': rt_top30,
        'ratingtop50': rt_top50,
        "function": "Rifler"
    }


def parse_individual_data(individualHtml):
    soup = BeautifulSoup(individualHtml, 'html.parser')

    overall_stats_container = soup.select(
        '.stats-rows .standard-box')[0]

    overall_stats = overall_stats_container.select('.stats-row span')
    kills = to_int(overall_stats[1].text.strip())
    deaths = to_int(overall_stats[3].text.strip())
    rounds_with_kills = to_float(overall_stats[9].text.strip())

    opening_stats_container = soup.select(
        '.stats-rows .standard-box')[1]

    opening_stats = opening_stats_container.select('.stats-row span')
    total_opening_kills = to_int(opening_stats[1].text.strip())
    total_opening_deaths = to_int(opening_stats[3].text.strip())
    opening_kill_ratio = to_float(opening_stats[5].text.strip())
    opening_kill_rating = to_float(opening_stats[7].text.strip())
    team_win_percentage_after_first_kill = to_float(
        opening_stats[9].text.strip("%"))
    first_kill_in_won_rounds = to_float(opening_stats[11].text.strip("%"))

    # Extract round stats
    round_stats_container = soup.select(
        '.stats-rows .standard-box')[2]

    round_stats = round_stats_container.select('.stats-row span')

    zero_kill_rounds = to_int(round_stats[1].text.strip())
    one_kill_rounds = to_int(round_stats[3].text.strip())
    two_kill_rounds = to_int(round_stats[5].text.strip())
    three_kill_rounds = to_int(round_stats[7].text.strip())
    four_kill_rounds = to_int(round_stats[9].text.strip())
    five_kill_rounds = to_int(round_stats[11].text.strip())

    # Extract weapon stats
    weapon_stats_container = soup.select(
        '.stats-rows .standard-box')[3]

    weapon_stats = weapon_stats_container.select('.stats-row span')

    rifle_kills = to_int(weapon_stats[1].text.strip())
    sniper_kills = to_int(weapon_stats[3].text.strip())
    smg_kills = to_int(weapon_stats[5].text.strip())
    pistol_kills = to_int(weapon_stats[7].text.strip())

    return {
        'kills': kills,
        'deaths': deaths,
        'roundsWithKills': rounds_with_kills,
        'totalOpeningKills': total_opening_kills,
        'totalOpeningDeaths': total_opening_deaths,
        'openingKillRatio': opening_kill_ratio,
        'openingKillRating': opening_kill_rating,
        'teamWinPercentageAfterFirstKill': team_win_percentage_after_first_kill,
        'firstKillInWonRounds': first_kill_in_won_rounds,
        'zeroKillRounds': zero_kill_rounds,
        'oneKillRounds': one_kill_rounds,
        'twoKillRounds': two_kill_rounds,
        'threeKillRounds': three_kill_rounds,
        'fourKillRounds': four_kill_rounds,
        'fiveKillRounds': five_kill_rounds,
        'rifleKills': rifle_kills,
        'sniperKills': sniper_kills,
        'smgKills': smg_kills,
        'pistolKills': pistol_kills,
    }


def merge_data(overall, individual):
    merged = overall.copy()
    merged["function"] = get_function(
        individual["rifleKills"], individual["sniperKills"])
    merged.update(individual)
    return merged


def get_function(rifle, awp):
    total = rifle + awp
    if awp / total >= 0.50:
        return "AWPer"
    else:
        return "Rifler"


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


def save_to_json(player_data, player_name):
    # Create the file name
    file_name = f"{player_name}"
    # Write the player data to the file
    with open(file_name, 'w') as f:
        json.dump(player_data, f, indent=4)

    print(f"Player data saved to {file_name}")


if __name__ == '__main__':
    main()
