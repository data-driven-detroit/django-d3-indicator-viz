/**
 * Test harness for chart-connector.js filter logic.
 *
 * Reproduces the type-mismatch bug: JSON data has string IDs ("42")
 * while dataset attributes are parsed with parseInt (42).
 *
 * Run: node tests/test_chart_filters.mjs
 */

let passed = 0;
let failed = 0;

function assert(condition, message) {
    if (condition) {
        console.log(`  PASS: ${message}`);
        passed++;
    } else {
        console.error(`  FAIL: ${message}`);
        failed++;
    }
}

// --- Simulate the data as it comes from Django's JSON serialization ---
// Custom indicators often serialize IDs as strings
const allValues = [
    { indicator_id: "10", source_id: "3", location_id: "FIPS_06", value: 42.5 },
    { indicator_id: "10", source_id: "3", location_id: "FIPS_01", value: 38.1 },
    { indicator_id: "10", source_id: "3", location_id: "FIPS_04", value: 40.0 },
    { indicator_id: 20,   source_id: 5,   location_id: 100,       value: 55.0 },  // numeric IDs
    { indicator_id: 20,   source_id: 5,   location_id: 200,       value: 60.0 },
];

// --- Simulate dataset attributes (always parsed with parseInt) ---
const indicatorId = 10;   // parseInt("10")
const sourceId = 3;       // parseInt("3")

// =====================================================================
// Test 1: OLD filter (strict ===) — demonstrates the bug
// =====================================================================
console.log("\n--- Old filter (strict ===, the bug) ---");

const oldResult = allValues.filter(v =>
    v.indicator_id === indicatorId && v.source_id === sourceId
);
assert(oldResult.length === 0,
    `String IDs vs Number: strict === returns 0 matches (got ${oldResult.length})`);

// =====================================================================
// Test 2: NEW filter (Number coercion) — the fix
// =====================================================================
console.log("\n--- New filter (Number coercion, the fix) ---");

const newResult = allValues.filter(v =>
    Number(v.indicator_id) === indicatorId && Number(v.source_id) === sourceId
);
assert(newResult.length === 3,
    `String IDs vs Number: Number() coercion returns 3 matches (got ${newResult.length})`);

// =====================================================================
// Test 3: Number coercion still works when both sides are already numbers
// =====================================================================
console.log("\n--- Number coercion with numeric JSON data ---");

const numericResult = allValues.filter(v =>
    Number(v.indicator_id) === 20 && Number(v.source_id) === 5
);
assert(numericResult.length === 2,
    `Numeric IDs: Number() coercion returns 2 matches (got ${numericResult.length})`);

// =====================================================================
// Test 4: Location ID filtering — old vs new
// =====================================================================
console.log("\n--- Location ID filtering ---");

const primaryLocation = { id: "FIPS_06" };

// Old: strict ===
const oldPrimary = newResult.filter(v => v.location_id === primaryLocation.id);
assert(oldPrimary.length === 1,
    `String===String location match works (got ${oldPrimary.length})`);

// New: String() coercion (handles mixed types)
const newPrimary = newResult.filter(v => String(v.location_id) === String(primaryLocation.id));
assert(newPrimary.length === 1,
    `String() coerced location match works (got ${newPrimary.length})`);

// Numeric location IDs (e.g. standard profiles use integer FIPS)
const numericPrimary = { id: 100 };
const numericLocResult = numericResult.filter(v =>
    String(v.location_id) === String(numericPrimary.id)
);
assert(numericLocResult.length === 1,
    `Numeric location_id with String() coercion works (got ${numericLocResult.length})`);

// =====================================================================
// Test 5: Comparison location filtering
// =====================================================================
console.log("\n--- Comparison location filtering ---");

const compareLocations = [{ id: "FIPS_01" }, { id: "FIPS_04" }];
const compareLocationIds = compareLocations.map(loc => String(loc.id));
const compareValues = newResult.filter(v =>
    compareLocationIds.includes(String(v.location_id))
);
assert(compareValues.length === 2,
    `Comparison locations filter returns 2 matches (got ${compareValues.length})`);

// With numeric IDs
const numCompare = [{ id: 200 }];
const numCompareIds = numCompare.map(loc => String(loc.id));
const numCompareValues = numericResult.filter(v =>
    numCompareIds.includes(String(v.location_id))
);
assert(numCompareValues.length === 1,
    `Numeric comparison location filter returns 1 match (got ${numCompareValues.length})`);

// =====================================================================
// Test 6: Edge case — NaN protection
// =====================================================================
console.log("\n--- Edge cases ---");

const badValues = [
    { indicator_id: "abc", source_id: "3", location_id: "X", value: 0 },
    { indicator_id: null, source_id: null, location_id: null, value: 0 },
];
const edgeResult = badValues.filter(v =>
    Number(v.indicator_id) === indicatorId && Number(v.source_id) === sourceId
);
assert(edgeResult.length === 0,
    `Non-numeric/null IDs don't accidentally match (got ${edgeResult.length})`);

// =====================================================================
// Summary
// =====================================================================
console.log(`\n${'='.repeat(50)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
if (failed > 0) {
    process.exit(1);
} else {
    console.log("All tests passed!");
}
