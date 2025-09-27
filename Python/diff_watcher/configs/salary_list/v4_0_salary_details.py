from diff_watcher.constants.paths import SALARY_LIST, ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED

v4_0_salary_details = {
	"desktop": {
		'values': f"{SALARY_LIST}/4.0-salary-details/4.0-salary-details.json",
		'template': f"{SALARY_LIST}/4.0-salary-details/desktop/4.0-salary-details_PC_(JJ).json",
		'render': [
			f"{SALARY_LIST}/4.0-salary-details/desktop/4.0-salary-details_PC (full).json",
			ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED,
		]
	},
	"mobile": {
		'values': f"{SALARY_LIST}/4.0-salary-details/4.0-salary-details.json",
		'template': f"{SALARY_LIST}/4.0-salary-details/mobile/4.0-salary-details_MOBILE_(JJ).json",
		'render': [
			f"{SALARY_LIST}/4.0-salary-details/mobile/4.0-salary-details_MOBILE (full).json",
			ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED,
		]
	}
}
