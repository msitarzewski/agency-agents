import { calcMA, calcEMA, calcBOLL, calcMACD, calcRSI, calcKDJ } from "../indicators";

describe("calcMA", () => {
  it("returns null for indices before period-1", () => {
    const result = calcMA([1, 2, 3, 4, 5], 3);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
  });

  it("computes correct simple moving average", () => {
    const result = calcMA([1, 2, 3, 4, 5], 3);
    expect(result[2]).toBe(2); // (1+2+3)/3
    expect(result[3]).toBe(3); // (2+3+4)/3
    expect(result[4]).toBe(4); // (3+4+5)/3
  });

  it("handles period equal to data length", () => {
    const result = calcMA([10, 20, 30], 3);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBe(20);
  });

  it("handles single element with period 1", () => {
    expect(calcMA([42], 1)).toEqual([42]);
  });

  it("returns all null when period exceeds data length", () => {
    expect(calcMA([1, 2], 5)).toEqual([null, null]);
  });
});

describe("calcEMA", () => {
  it("returns null before period-1", () => {
    const result = calcEMA([1, 2, 3, 4, 5], 3);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
  });

  it("first EMA value equals SMA of first period values", () => {
    const result = calcEMA([1, 2, 3, 4, 5], 3);
    expect(result[2]).toBe(2); // SMA seed: (1+2+3)/3
  });

  it("subsequent values use exponential smoothing", () => {
    const result = calcEMA([1, 2, 3, 4, 5], 3);
    // k = 2/(3+1) = 0.5
    // EMA[3] = 4 * 0.5 + 2 * 0.5 = 3.0
    expect(result[3]).toBe(3);
    // EMA[4] = 5 * 0.5 + 3 * 0.5 = 4.0
    expect(result[4]).toBe(4);
  });

  it("handles empty array", () => {
    expect(calcEMA([], 3)).toEqual([]);
  });
});

describe("calcBOLL", () => {
  const data = Array.from({ length: 25 }, (_, i) => 100 + i);

  it("returns null for upper/lower/mid before period", () => {
    const { upper, mid, lower } = calcBOLL(data, 20);
    expect(mid[18]).toBeNull();
    expect(upper[18]).toBeNull();
    expect(lower[18]).toBeNull();
  });

  it("mid equals SMA at period boundary", () => {
    const { mid } = calcBOLL(data, 20);
    // SMA of [100..119] = 109.5
    expect(mid[19]).toBeCloseTo(109.5, 4);
  });

  it("upper > mid > lower for varying data", () => {
    const { upper, mid, lower } = calcBOLL(data, 20);
    for (let i = 19; i < 25; i++) {
      if (mid[i] !== null) {
        expect(upper[i]!).toBeGreaterThan(mid[i]!);
        expect(lower[i]!).toBeLessThan(mid[i]!);
      }
    }
  });

  it("upper and lower are symmetric around mid", () => {
    const { upper, mid, lower } = calcBOLL(data, 20, 2);
    const i = 19;
    const bandUp = upper[i]! - mid[i]!;
    const bandDn = mid[i]! - lower[i]!;
    expect(bandUp).toBeCloseTo(bandDn, 10);
  });
});

describe("calcMACD", () => {
  const data = Array.from({ length: 50 }, (_, i) => 100 + Math.sin(i / 5) * 10);

  it("returns null DIF before slow period", () => {
    const { dif } = calcMACD(data);
    expect(dif[24]).toBeNull(); // slow=26, so dif[0..24] are null
  });

  it("DIF exists after slow period", () => {
    const { dif } = calcMACD(data);
    expect(dif[25]).not.toBeNull();
  });

  it("signal line exists after enough DIF values", () => {
    const { signal } = calcMACD(data);
    const firstSignal = signal.findIndex((v) => v !== null);
    expect(firstSignal).toBeGreaterThanOrEqual(25);
    expect(firstSignal).toBeLessThan(45);
  });

  it("histogram = dif - signal where both exist", () => {
    const { dif, signal, histogram } = calcMACD(data);
    for (let i = 0; i < data.length; i++) {
      if (dif[i] !== null && signal[i] !== null) {
        expect(histogram[i]).toBeCloseTo(dif[i]! - signal[i]!, 10);
      }
    }
  });
});

describe("calcRSI", () => {
  it("returns null for first period entries", () => {
    const data = Array.from({ length: 20 }, (_, i) => 100 + i);
    const result = calcRSI(data, 14);
    for (let i = 0; i < 14; i++) expect(result[i]).toBeNull();
  });

  it("RSI is between 0 and 100", () => {
    const data = Array.from({ length: 50 }, (_, i) => 100 + Math.sin(i) * 5);
    const result = calcRSI(data, 14);
    result.forEach((v) => {
      if (v !== null) {
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(100);
      }
    });
  });

  it("all-up data gives RSI = 100", () => {
    const data = Array.from({ length: 20 }, (_, i) => 100 + i);
    const result = calcRSI(data, 14);
    expect(result[14]).toBe(100);
  });

  it("all-down data gives RSI = 0", () => {
    const data = Array.from({ length: 20 }, (_, i) => 100 - i);
    const result = calcRSI(data, 14);
    expect(result[14]).toBe(0);
  });

  it("returns all null when data length < period+1", () => {
    const result = calcRSI([1, 2, 3], 14);
    expect(result.every((v) => v === null)).toBe(true);
  });
});

describe("calcKDJ", () => {
  const highs  = [110, 112, 108, 115, 120, 118, 122, 125, 119, 121];
  const lows   = [ 95,  98,  96, 100, 105, 102, 108, 110, 104, 107];
  const closes = [105, 110, 100, 112, 118, 105, 120, 122, 110, 119];

  it("returns null for indices before period-1", () => {
    const { k, d, j } = calcKDJ(highs, lows, closes, 9);
    for (let i = 0; i < 8; i++) {
      expect(k[i]).toBeNull();
      expect(d[i]).toBeNull();
      expect(j[i]).toBeNull();
    }
  });

  it("produces non-null K, D, J from period-1 onward", () => {
    const { k, d, j } = calcKDJ(highs, lows, closes, 9);
    expect(k[8]).not.toBeNull();
    expect(d[8]).not.toBeNull();
    expect(j[8]).not.toBeNull();
  });

  it("J = 3K - 2D", () => {
    const { k, d, j } = calcKDJ(highs, lows, closes, 9);
    for (let i = 8; i < closes.length; i++) {
      expect(j[i]).toBeCloseTo(3 * k[i]! - 2 * d[i]!, 10);
    }
  });

  it("K and D are between 0 and 100", () => {
    const { k, d } = calcKDJ(highs, lows, closes, 9);
    k.forEach((v) => {
      if (v !== null) {
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(100);
      }
    });
    d.forEach((v) => {
      if (v !== null) {
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(100);
      }
    });
  });

  it("returns all null when data shorter than period", () => {
    const { k, d, j } = calcKDJ([110], [95], [105], 9);
    expect(k[0]).toBeNull();
    expect(d[0]).toBeNull();
    expect(j[0]).toBeNull();
  });
});
