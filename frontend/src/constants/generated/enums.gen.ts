/* eslint-disable */
// AUTO-GENERATED FILE. DO NOT EDIT.

export enum GenderEnum {
  MALE = "male",
  FEMALE = "female",
  OTHER = "other",
  UNDISCLOSED = "undisclosed",
}

export const GenderEnumValues = [
  "male",
  "female",
  "other",
  "undisclosed",
] as const

export type GenderEnumValue = (typeof GenderEnumValues)[number]

export enum UserTagStatusEnum {
  EXPIRED = -1,
  PENDING = 0,
  ACTIVE = 1,
}

export const UserTagStatusEnumValues = [
  -1,
  0,
  1,
] as const

export type UserTagStatusEnumValue = (typeof UserTagStatusEnumValues)[number]

export const ENUM_NAMES = [
  "GenderEnum",
  "UserTagStatusEnum",
] as const
