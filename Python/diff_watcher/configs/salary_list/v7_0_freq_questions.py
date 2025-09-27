from diff_watcher.constants.paths import SALARY_LIST

v7_0_frequent_questions = {
	"desktop": {
		'values': f"{SALARY_LIST}/7.0-frequent-questions | (Частые вопросы)/7.0-frequent-questions.json",
		'template': f"{SALARY_LIST}/7.0-frequent-questions | (Частые вопросы)/desktop/7.0-frequent-questions_PC.json",
		'render': [
			f"{SALARY_LIST}/7.0-frequent-questions | (Частые вопросы)/desktop/7.0-frequent-questions_PC (full).json",
		]
	},
	"mobile": {
		'values': f"{SALARY_LIST}/7.0-frequent-questions | (Частые вопросы)/7.0-frequent-questions.json",
		'template': f"{SALARY_LIST}/7.0-frequent-questions | (Частые вопросы)/mobile/7.0-frequent-questions_MOBILE.json",
		'render': [
			f"{SALARY_LIST}/7.0-frequent-questions | (Частые вопросы)/mobile/7.0-frequent-questions_MOBILE (full).json",
		]
	}
}
