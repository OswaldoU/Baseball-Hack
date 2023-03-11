import pandas as pd
import cplex
import docplex.mp.model as cpx
import argparse
import matplotlib.pyplot as plt

def _check_roster_possible():
	total_salaries = []
	df_check = df[df['yearID'] == args.year]
	for position, num in zip(positions,[1, 1, 1, 1, 1, 1, 3]):
		total_salaries += list(df_check[df_check['POS'] == position].nsmallest(num, 'SalaryInMillions')['SalaryInMillions'])
	return sum(total_salaries) <= args.payroll

def _solve_model():
    model = cpx.Model(name='Baseball Model')

    players = list(df['FullName'].unique())
    salaries = {f'{row.FullName}_{row.POS}' : row.SalaryInMillions for _, row in df.iterrows()}
    stats = stats = {f'{row.FullName}_{row.POS}' : row[args.stat] for _, row in df.iterrows()}

    ### VARIABLES ###
    variables = {}
    position_players_vars = {pos : [] for pos in positions}
    players_position_vars = {player : [] for player in players}
    for player in players:
        player_positions = list(set(df[df['FullName'] == player]['POS']))
        for pos in player_positions:
            variable = model.binary_var(name=f'{player}_{pos}')
            players_position_vars[player].append(variable)
            position_players_vars[pos].append(variable)
            variables[f'{player}_{pos}'] = variable

    ### CONSTRAINTS ###
    # Ensure that number of overall players selected is 9
    model.add_constraint(ct=(model.sum(player_var for player_var in variables.values()) == 9))
    # Ensure each position is only allowed the allotted number of players
    for position in positions:
        min_value = 3 if position == 'OF' else 1
        model.add_constraint(ct=(model.sum(player_var for player_var in position_players_vars[position])) == min_value)
    # Ensure that each player is selected at most once
    for player in players:
        model.add_constraint(ct=(model.sum(player_var for player_var in players_position_vars[player]) <= 1))
    # Ensure that salary total is less than or equal to payroll
    model.add_constraint(ct=(model.sum(player_var * salaries[player_name] for player_name, player_var in variables.items()) <= args.payroll))

    ### OBJECTIVE ###
    objective = model.sum(player_var * stats[player_name] for player_name, player_var in variables.items())
    model.set_objective('max', objective)

    ### SOLVE ###
    solution = model.solve()

    # Get the gap
    gap = model.solve_details.mip_relative_gap

    assert solution

    # Get results and solve second model to get position of players
    lineup = [variable for variable in variables if solution.get_value(variable) == 1]

    total_salary_used = sum([salaries[player] for player in lineup])
    total_stat = solution.get_objective_value()

    final_positions = {}
    final_player_salaries = {}
    final_player_stats = {}
    OF_ID = 1
    for player in lineup:
        name, position = player.split('_')
        if position == 'OF':
            position = f'{position}_{OF_ID}'
            OF_ID += 1
        final_positions[position] = name
        player_salary = list(df[df['FullName'] == name]['SalaryInMillions'])[0]
        player_stat = list(df[df['FullName'] == name][args.stat])[0]
        final_player_salaries[name] = round(player_salary,2)
        final_player_stats[name] = int(player_stat)

    return final_positions, final_player_stats, final_player_salaries, total_salary_used, total_stat, gap
def _solve_model():
    model = cpx.Model(name='Baseball Model')

    players = list(df['FullName'].unique())
    salaries = {f'{row.FullName}_{row.POS}' : row.SalaryInMillions for _, row in df.iterrows()}
    stats = stats = {f'{row.FullName}_{row.POS}' : row[args.stat] for _, row in df.iterrows()}

    ### VARIABLES ###
    variables = {}
    position_players_vars = {pos : [] for pos in positions}
    players_position_vars = {player : [] for player in players}
    for player in players:
        player_positions = list(set(df[df['FullName'] == player]['POS']))
        for pos in player_positions:
            variable = model.binary_var(name=f'{player}_{pos}')
            players_position_vars[player].append(variable)
            position_players_vars[pos].append(variable)
            variables[f'{player}_{pos}'] = variable

    ### CONSTRAINTS ###
    # Ensure that number of overall players selected is 9
    model.add_constraint(ct=(model.sum(player_var for player_var in variables.values()) == 9))
    # Ensure each position is only allowed the allotted number of players
    for position in positions:
        min_value = 3 if position == 'OF' else 1
        model.add_constraint(ct=(model.sum(player_var for player_var in position_players_vars[position])) == min_value)
    # Ensure that each player is selected at most once
    for player in players:
        model.add_constraint(ct=(model.sum(player_var for player_var in players_position_vars[player]) <= 1))
    # Ensure that salary total is less than or equal to payroll
    model.add_constraint(ct=(model.sum(player_var * salaries[player_name] for player_name, player_var in variables.items()) <= args.payroll))

    ### OBJECTIVE ###
    objective = model.sum(player_var * stats[player_name] for player_name, player_var in variables.items())
    model.set_objective('max', objective)

    ### SOLVE ###
    solution = model.solve()

    # Get the gap
    gap = model.solve_details.mip_relative_gap
    assert solution

    # Get results and solve second model to get position of players
    lineup = [variable for variable in variables if solution.get_value(variable) == 1]

    total_salary_used = sum([salaries[player] for player in lineup])
    total_stat = solution.get_objective_value()

    final_positions = {}
    final_player_salaries = {}
    final_player_stats = {}
    OF_ID = 1
    for player in lineup:
        name, position = player.split('_')
        if position == 'OF':
            position = f'{position}_{OF_ID}'
            OF_ID += 1
        final_positions[position] = name
        player_salary = list(df[df['FullName'] == name]['SalaryInMillions'])[0]
        player_stat = list(df[df['FullName'] == name][args.stat])[0]
        final_player_salaries[name] = round(player_salary,2)
        final_player_stats[name] = int(player_stat)

    return gap, final_positions, final_player_stats, final_player_salaries, total_salary_used, total_stat

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-data_csv', '--data_csv', type=str, default='data.csv')
	parser.add_argument('-year', '--year', type=int, default=2002)
	parser.add_argument('-payroll', '--payroll', type=int, default=19) # in millions
	parser.add_argument('-stat', '--stat', type=str, default='HR')
	args = parser.parse_args()

	df = pd.read_csv(args.data_csv)

	available_years = list(df['yearID'].unique())
	available_stas = ['G', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'SO', 'IBB', 'HBP', 'SH', 'SF', 'GIDP']
	positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']

	assert args.year in available_years, 'Year not Available'
	assert args.stat in available_stas, 'Stat not Available'
	assert _check_roster_possible(), 'Feasible lineup not feasibile for payroll'

	df = df[df['yearID'] == args.year]

	gap, final_positions, final_player_stats, final_player_salaries, total_salary_used, total_stat = _solve_model()

	print('===')
	print('Lineup:')
	for position in positions:
		if position == 'OF':
			print(f'({position}) {final_positions[f"{position}_1"]} - {final_player_stats[final_positions[f"{position}_1"]]} {args.stat} (${final_player_salaries[final_positions[f"{position}_1"]]}m)')
			print(f'({position}) {final_positions[f"{position}_2"]} - {final_player_stats[final_positions[f"{position}_1"]]} {args.stat} (${final_player_salaries[final_positions[f"{position}_2"]]}m)')
			print(f'({position}) {final_positions[f"{position}_3"]} - {final_player_stats[final_positions[f"{position}_1"]]} {args.stat} (${final_player_salaries[final_positions[f"{position}_3"]]}m)')
		else:
			print(f'({position}) {final_positions[position]} - {final_player_stats[final_positions[f"{position}"]]} {args.stat} (${final_player_salaries[final_positions[f"{position}"]]}m)')
	print('----------------')
	print(f'Totals: {int(total_stat)} {args.stat} (${total_salary_used}m)')
	print(f'Gap from the optimal solution: {gap}')

	# player_names = [final_player_stats.keys()]

	# Create the pie chart
	# plt.pie(list(final_player_stats.keys()), labels=list(final_player_stats.values()))

