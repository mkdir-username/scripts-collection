from diff_watcher.constants.paths import SALARY_LIST, ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED

v3_0_salary_data = {
	"desktop": {
		'values': f"{SALARY_LIST}/3.0-salary-list | (Список зп, 1 работодатель)/3.0-salary-list.json",
		'template': f"{SALARY_LIST}/3.0-salary-list | (Список зп, 1 работодатель)/desktop/3.0-salary-list_PC_(JJ).json",
		'render': [
			f"{SALARY_LIST}/3.0-salary-list | (Список зп, 1 работодатель)/desktop/3.0-salary-list_PC (full).json",
			ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED,
		]
	},
	"mobile": {
		'values': f"{SALARY_LIST}/3.0-salary-list | (Список зп, 1 работодатель)/3.0-salary-list.json",
		'template': f"{SALARY_LIST}/3.0-salary-list | (Список зп, 1 работодатель)/mobile/3.0-salary-list_MOBILE_(JJ).json",
		'render': [
			f"{SALARY_LIST}/3.0-salary-list | (Список зп, 1 работодатель)/mobile/3.0-salary-list_MOBILE (full).json",
			ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED,
		]
	}
}
