from diff_watcher.constants.paths import SALARY_LIST, ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED

v3_1_salary_data = {
	"desktop": {
		'values': f"{SALARY_LIST}/3.1-salary-list | (Несколько работодателей)/3.1-salary-list.json",
		'template': f"{SALARY_LIST}/3.1-salary-list | (Несколько работодателей)/desktop/3.1-salary-list_PC_(JJ).json",
		'render': [
			f"{SALARY_LIST}/3.1-salary-list | (Несколько работодателей)/desktop/3.1-salary-list_PC (full).json",
			ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED,
		]
	},
	"mobile": {
		'values': f"{SALARY_LIST}/3.1-salary-list | (Несколько работодателей)/3.1-salary-list.json",
		'template': f"{SALARY_LIST}/3.1-salary-list | (Несколько работодателей)/mobile/3.1-salary-list_MOBILE_(JJ).json",
		'render': [
			f"{SALARY_LIST}/3.1-salary-list | (Несколько работодателей)/mobile/3.1-salary-list_MOBILE (full).json",
			ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED,
		]
	}
}
