import {
  GenderEnum,
  type GenderEnumValue,
  UserTagStatusEnum,
  type UserTagStatusEnumValue,
} from "./generated/enums.gen";

export type GenderValue = GenderEnumValue;
export { GenderEnum, UserTagStatusEnum };

export const GENDER_LABELS: Record<GenderValue, string> = {
  [GenderEnum.MALE]: "男",
  [GenderEnum.FEMALE]: "女",
  [GenderEnum.OTHER]: "其他",
  [GenderEnum.UNDISCLOSED]: "不透露",
};

export const GENDER_OPTIONS = [
  { label: GENDER_LABELS[GenderEnum.MALE], value: GenderEnum.MALE },
  { label: GENDER_LABELS[GenderEnum.FEMALE], value: GenderEnum.FEMALE },
  { label: GENDER_LABELS[GenderEnum.OTHER], value: GenderEnum.OTHER },
  { label: GENDER_LABELS[GenderEnum.UNDISCLOSED], value: GenderEnum.UNDISCLOSED },
] as const;

export type UserTagStatusValue = UserTagStatusEnumValue;

export const USER_TAG_STATUS_LABELS: Record<UserTagStatusValue, string> = {
  [UserTagStatusEnum.EXPIRED]: "已过期",
  [UserTagStatusEnum.PENDING]: "待生效",
  [UserTagStatusEnum.ACTIVE]: "生效中",
};

export const USER_TAG_STATUS_TYPES: Record<
  UserTagStatusValue,
  "success" | "warning" | "info"
> = {
  [UserTagStatusEnum.EXPIRED]: "info",
  [UserTagStatusEnum.PENDING]: "warning",
  [UserTagStatusEnum.ACTIVE]: "success",
};
