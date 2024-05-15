export type StakingRewardsInfo = {
  mechRequestCount: number;
  serviceInfo: unknown[];
  livenessPeriod: number;
  livenessRatio: number;
  rewardsPerSecond: number;
  isEligibleForRewards: boolean;
  availableRewardsForEpoch: number;
};