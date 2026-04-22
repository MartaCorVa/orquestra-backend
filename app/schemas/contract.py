from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, model_validator


class ContractBase(BaseModel):
    weekly_hours: int
    daily_hours: int
    min_days_off_per_week: int = 2

    work_monday: bool = True
    work_tuesday: bool = True
    work_wednesday: bool = True
    work_thursday: bool = True
    work_friday: bool = True
    work_saturday: bool = False
    work_sunday: bool = False

    has_fixed_schedule: bool = False
    preferred_start_time: time | None = None
    preferred_end_time: time | None = None

    active: bool = True
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode = "after")
    def validate_contract(self):
        if self.weekly_hours <= 0:
            raise ValueError("weekly_hours must be greater than 0")

        if self.daily_hours <= 0:
            raise ValueError("daily_hours must be greater than 0")

        if self.min_days_off_per_week < 0 or self.min_days_off_per_week > 7:
            raise ValueError("min_days_off_per_week must be between 0 and 7")

        if self.end_date is not None and self.start_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")

        if self.has_fixed_schedule:
            if self.preferred_start_time is None or self.preferred_end_time is None:
                raise ValueError(
                    "preferred_start_time and preferred_end_time are required when has_fixed_schedule is true"
                )

            if self.preferred_end_time <= self.preferred_start_time:
                raise ValueError("preferred_end_time must be later than preferred_start_time")

        return self


class ContractCreate(ContractBase):
    employee_id: int


class ContractCreateOnboarding(ContractBase):
    weekly_hours: int
    daily_hours: int
    min_days_off_per_week: int

    work_monday: bool
    work_tuesday: bool
    work_wednesday: bool
    work_thursday: bool
    work_friday: bool
    work_saturday: bool
    work_sunday: bool

    has_fixed_schedule: bool
    preferred_start_time: time | None = None
    preferred_end_time: time | None = None

    active: bool
    start_date: date
    end_date: date | None = None


class ContractUpdate(BaseModel):
    weekly_hours: int | None = None
    daily_hours: int | None = None
    min_days_off_per_week: int | None = None

    work_monday: bool | None = None
    work_tuesday: bool | None = None
    work_wednesday: bool | None = None
    work_thursday: bool | None = None
    work_friday: bool | None = None
    work_saturday: bool | None = None
    work_sunday: bool | None = None

    has_fixed_schedule: bool | None = None
    preferred_start_time: time | None = None
    preferred_end_time: time | None = None

    active: bool | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode = "after")
    def validate_contract_update(self):
        if self.weekly_hours is not None and self.weekly_hours <= 0:
            raise ValueError("weekly_hours must be greater than 0")

        if self.daily_hours is not None and self.daily_hours <= 0:
            raise ValueError("daily_hours must be greater than 0")

        if self.min_days_off_per_week is not None:
            if self.min_days_off_per_week < 0 or self.min_days_off_per_week > 7:
                raise ValueError("min_days_off_per_week must be between 0 and 7")

        if self.end_date is not None and self.start_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")

        if self.has_fixed_schedule is True:
            if self.preferred_start_time is None or self.preferred_end_time is None:
                raise ValueError(
                    "preferred_start_time and preferred_end_time are required when has_fixed_schedule is true"
                )

        if (
            self.preferred_start_time is not None
            and self.preferred_end_time is not None
            and self.preferred_end_time <= self.preferred_start_time
        ):
            raise ValueError("preferred_end_time must be later than preferred_start_time")

        return self


class ContractResponse(ContractBase):
    id: int
    employee_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)