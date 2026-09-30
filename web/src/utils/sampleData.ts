/**
 * Sample dataset generator for SynPassport assurance demonstration.
 * Generates a realistic heart disease benchmark dataset with a 65+ subgroup.
 */

export function generateHeartDiseaseSampleCsv(): string {
  const headers = "age,cholesterol,resting_bp,target\n";
  const rows = [
    // Subgroup: age < 65
    "28,180.0,118,0",
    "32,190.0,122,0",
    "35,195.0,120,0",
    "41,210.0,128,1",
    "44,215.0,130,0",
    "48,225.0,135,1",
    "52,230.0,138,1",
    "55,240.0,140,1",
    "58,245.0,142,0",
    "61,250.0,145,1",
    "33,185.0,119,0",
    "39,205.0,126,0",
    "45,220.0,132,1",
    "49,228.0,136,1",
    "54,235.0,138,0",
    "57,242.0,140,1",
    "60,248.0,144,1",
    "62,252.0,146,0",
    "63,255.0,148,1",
    "64,258.0,150,1",
    // Subgroup: age >= 65 (N=15, triggering INSUFFICIENT_EVIDENCE when clinical_ml needs N>=171)
    "65,260.0,152,1",
    "66,262.0,150,1",
    "67,265.0,154,1",
    "68,270.0,155,1",
    "69,268.0,152,0",
    "70,275.0,158,1",
    "71,272.0,154,1",
    "72,280.0,160,1",
    "73,278.0,156,0",
    "74,282.0,162,1",
    "75,285.0,164,1",
    "76,288.0,165,1",
    "77,290.0,166,1",
    "78,295.0,168,1",
    "80,300.0,170,1",
  ];
  return headers + rows.join("\n") + "\n";
}
