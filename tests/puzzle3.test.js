const axios = require('axios');
const { generateCryptoPayload } = require('../src/specialists/crypto_specialist');
const { generateSportPayload } = require('../src/specialists/sport_specialist');
const { generateMacroPayload } = require('../src/specialists/macro_specialist');
const { validatePayload } = require('../src/agents/payload_guard');

jest.mock('axios');

describe('PUZZLE 3 — SPECIALIST DOMAIN AGENTS', () => {

  afterEach(() => {
    jest.clearAllMocks();
    delete process.env.FRED_API_KEY;
  });

  describe('CRYPTO-SPEC', () => {
    test('should generate valid payload from Binance data', async () => {
      axios.get.mockImplementation((url) => {
        if (url.includes('klines')) {
          return Promise.resolve({
            data: Array(200).fill([0, 0, 0, 0, "100", 0, 0, 0, 0, 0, 0, 0])
          });
        }
        if (url.includes('ticker')) {
          return Promise.resolve({
            data: {
              volume: "1000",
              weightedAvgPrice: "100",
              priceChangePercent: "5",
              count: "5000"
            }
          });
        }
      });

      const payload = await generateCryptoPayload('BTCUSDT');
      expect(payload.degraded_mode).toBeUndefined(); // Check top level if nested in stochastic_calibration
      expect(payload.stochastic_calibration.degraded_mode).toBe(false);
      expect(payload.state_vector.length).toBe(15);

      const validation = validatePayload(payload);
      expect(validation.valid).toBe(true);
    });

    test('should enter degraded mode on API failure', async () => {
      axios.get.mockRejectedValue(new Error('Network Error'));
      const payload = await generateCryptoPayload('BTCUSDT');
      expect(payload.stochastic_calibration.degraded_mode).toBe(true);
      expect(payload.signal.direction).toBe('neutral');
    });
  });

  describe('SPORT-SPEC', () => {
    test('should generate valid payload from SportsDB data', async () => {
      axios.get.mockResolvedValue({
        data: {
          results: [
            { idHomeTeam: '133602', intHomeScore: '2', intAwayScore: '0' },
            { idHomeTeam: '133602', intHomeScore: '3', intAwayScore: '1' },
            { idHomeTeam: '133602', intHomeScore: '1', intAwayScore: '0' },
            { idHomeTeam: '133602', intHomeScore: '2', intAwayScore: '2' },
            { idHomeTeam: '133602', intHomeScore: '0', intAwayScore: '1' }
          ]
        }
      });

      const payload = await generateSportPayload('133602');
      expect(payload.stochastic_calibration.degraded_mode).toBe(false);
      expect(payload.fairs_vector.regime.classifier).toBe('event-driven');

      const validation = validatePayload(payload);
      expect(validation.valid).toBe(true);
    });
  });

  describe('MACRO-SPEC', () => {
    test('should generate valid payload when API key is present', async () => {
      process.env.FRED_API_KEY = 'mock-key';
      axios.get.mockResolvedValue({
        data: {
          observations: [
            { value: '4.0' },
            { value: '4.2' }
          ]
        }
      });

      const payload = await generateMacroPayload('UNRATE');
      expect(payload.stochastic_calibration.degraded_mode).toBe(false);
      expect(payload.fairs_vector.regime.classifier).toBe('macro-driven');

      const validation = validatePayload(payload);
      expect(validation.valid).toBe(true);
    });

    test('should enter degraded mode when API key is missing', async () => {
      delete process.env.FRED_API_KEY;
      const payload = await generateMacroPayload('UNRATE');
      expect(payload.stochastic_calibration.degraded_mode).toBe(true);
    });
  });
});
