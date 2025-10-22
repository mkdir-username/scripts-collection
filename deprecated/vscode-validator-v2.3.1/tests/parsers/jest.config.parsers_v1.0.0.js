/**
 * Jest configuration for parser tests
 * @version 1.0.0
 */

export default {
  displayName: 'parsers',
  preset: 'ts-jest/presets/default-esm',
  testEnvironment: 'node',

  // Test matching
  testMatch: [
    '**/tests/parsers/**/*.test.ts',
    '**/tests/parsers/**/*.spec.ts',
  ],

  // Transform
  extensionsToTreatAsEsm: ['.ts'],
  transform: {
    '^.+\\.ts$': [
      'ts-jest',
      {
        useESM: true,
        tsconfig: {
          target: 'ES2022',
          module: 'ES2022',
          moduleResolution: 'node',
          strict: true,
          esModuleInterop: true,
          allowSyntheticDefaultImports: true,
          resolveJsonModule: true,
          isolatedModules: true,
        },
      },
    ],
  },

  // Module resolution
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1',
  },

  // Coverage
  collectCoverageFrom: [
    'src/parsers/**/*.ts',
    '!src/parsers/**/*.test.ts',
    '!src/parsers/**/*.spec.ts',
    '!src/parsers/**/*.d.ts',
  ],

  coverageDirectory: '<rootDir>/coverage/parsers',

  coverageThresholds: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },

  // Setup
  setupFilesAfterEnv: ['<rootDir>/tests/parsers/setup.ts'],

  // Timeouts
  testTimeout: 10000,

  // Reporting
  verbose: true,
  bail: false,
  errorOnDeprecated: true,

  // Cache
  cache: true,
  cacheDirectory: '<rootDir>/.tmp/jest-cache/parsers',

  // Performance
  maxWorkers: '50%',
  maxConcurrency: 5,

  // Clear mocks between tests
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
};
