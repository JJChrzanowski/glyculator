import numpy as np
import pandas as pd
import scipy

from .utils import DT, GLUCOSE
from .configs import CalcConfig


class GVIndex():
    def __init__(self, df: pd.DataFrame, calc_config: CalcConfig):
        self.df = self.set_df(df)
        self.calc_config = self.set_calc_config(calc_config)

    def calculate(self):
        raise NotImplementedError

    def set_df(self, df: pd.DataFrame):
        if(not isinstance(df, pd.core.frame.DataFrame)):
            raise ValueError("df needs to be a pandas DataFrame")

        return df

    def set_calc_config(self, calc_config: CalcConfig):
        if(not isinstance(calc_config, CalcConfig)):
            raise ValueError("calc_config needs to be a CalcConfig")

        return calc_config


class GVMean(GVIndex):
    def __init__(self, **kwargs):
        super(GVMean, self).__init__(**kwargs)

    def calculate(self):
        return np.nanmean(self.df[GLUCOSE])
    

class GVMedian(GVIndex):
    def __init__(self, **kwargs):
        super(GVMedian, self).__init__(**kwargs)

    def calculate(self):
        return np.nanmedian(self.df[GLUCOSE])


class GVVariance(GVIndex):
    def __init__(self, **kwargs):
        super(GVVariance, self).__init__(**kwargs)

    def calculate(self):
        return np.nanvar(self.df[GLUCOSE])


class GVNanFraction(GVIndex):
    def __init__(self, **kwargs):
        super(GVNanFraction, self).__init__(**kwargs)

    def calculate(self):
        return np.nansum(np.isnan(self.df[GLUCOSE])) / len(self.df)


class GVRecordsNo(GVIndex):
    def __init__(self, **kwargs):
        super(GVRecordsNo, self).__init__(**kwargs)

    def calculate(self):
        return len(self.df)


class GVCV(GVIndex):
    def __init__(self, **kwargs):
        super(GVCV, self).__init__(**kwargs)

    def calculate(self):
        return np.nanvar(self.df[GLUCOSE]) / np.nanmean(self.df[GLUCOSE])


class GVstd(GVIndex):
    def __init__(self, **kwargs):
        super(GVstd, self).__init__(**kwargs)

    def calculate(self):
        return np.nanstd(self.df[GLUCOSE])


class GVm100(GVIndex):
    def __init__(self, **kwargs):
        super(GVm100, self).__init__(**kwargs)

    def calculate(self):
        if(self.calc_config == "mg"):
            # np.ma.array is numpy built-in mask function
            # numpy functions will mask elements that are inf in
            # calculations with masked array
            return np.nanmean(1000 * np.log10(np.ma.array(self.df[GLUCOSE]) / 100))
        if(self.calc_config == "mmol"):
            # glucose: mmol/l * 18 = mg/dl
            return np.nanmean(1000 * np.log10(np.ma.array(self.df[GLUCOSE]) / (100 / 18)))


class GVj(GVIndex):
    def __init__(self, **kwargs):
        super(GVj, self).__init__(**kwargs)

    def calculate(self):
        return 0.001 * np.power(np.nanmean(self.df[GLUCOSE]) + np.nanstd(self.df[GLUCOSE]), 2)


class GVmage(GVIndex):
    def __init__(self, **kwargs):
        super(GVmage, self).__init__(**kwargs)

    def calculate(self):
        """Calculates MAGE (mean average of glucose excursions)

        Steps undertaken:
        1. Replace nans with mean
        2. Moving average with window size equal to 9
        3. Search excursions and calculate the average

        Returns:
            float:
                value of MAGE

        """
        nans_replaced = self.df[GLUCOSE].replace(to_replace=np.nan, value=np.nanmean(self.df[GLUCOSE]))
        smoothed = self._moving_average(nans_replaced,
            window=self.calc_config.mage_moving_average_window_size)

        

        return "mage-placeholder" # TODO (konrad.pagacz@gmail.com) implement mage

    def _moving_average(self, arr: pd.Series, window: int):
        """Calculates moving average smoothing.

        Arguments:
            arr (pandas.Series):
                pandas.Series of glucose values
            window (int):
                size of the moving average window

        Returns:
            pandas.Series
                Series with smoothed glucose values.

        Raises:
            ValueError:
                if arr is not a pandas.Series
            ValueError:
                if window is not int
        
        """
        if(not isinstance(arr, pd.core.series.Series)):
            raise ValueError("arr must be a pandas.Series")

        if(type(window) != int):
            raise ValueError("window must be an int")

        return np.convolve(a=arr, v=np.ones((window,)) / window, mode="valid")


class GVmodd(GVIndex):
    def __init__(self, **kwargs):
        super(GVmodd, self).__init__(**kwargs)

    def calculate(self):
        daily_differences = np.diff(self.df[GLUCOSE], n=24 * 60 / self.calc_config.interval)
        return np.nanmean(daily_differences)


class GVcongaX(GVIndex):
    def __init__(self, **kwargs):
        super(GVcongaX, self).__init__(**kwargs)

    def calculate(self, hours: int):
        if(type(hours) != int):
            raise ValueError("hours must be int")
        differences = np.diff(self.df[GLUCOSE], n=hours * 60 / self.calc_config.interval)
        return np.nanvar(differences)

    def __call__(self, hours: int, **kwargs):
        if(type(hours) != int):
            raise ValueError("hours must be int")
        df = kwargs.pop("df")
        calc_config = kwargs.pop("calc_config")
        differences = np.diff(df[GLUCOSE], n=hours * 60 / calc_config.interval)
        return np.nanvar(differences)   


class GVhypoglycemia(GVIndex):
    def __init__(self, **kwargs):
        super(GVhypoglycemia, self).__init__(**kwargs)

    def calculate(self, threshold: int):
        if(type(threshold) != int):
            raise ValueError("threshold must be int")
        
        return np.nansum(self.df[GLUCOSE] < threshold)


class GVhyperglycemia(GVIndex):
    def __init__(self, **kwargs):
        super(GVhyperglycemia, self).__init__(**kwargs)

    def calculate(self, threshold: int):
        if(type(threshold) != int):
            raise ValueError("threshold must be int")

        return np.nansum(self.df[GLUCOSE] > threshold)


class GVgrade(GVIndex):
    def __init__(self, **kwargs):
        super(GVgrade, self).__init__(**kwargs)

    def calculate(self):
        if(self.calc_config.unit == "mg"):
            GRADEs = 425 * np.power(np.log10(np.log10(self.df[GLUCOSE] / 18) + 0.16), 2)

        if(self.calc_config.unit == "mmol"):
            GRADEs = 425 * np.power(np.log10(np.log10(self.df[GLUCOSE]) + 0.16), 2)

        return np.nanmean(GRADEs)


class GVgrade_hypo(GVIndex):
    def __init__(self, **kwargs):
        super(GVgrade_hypo, self).__init__(**kwargs)

    def calculate(self):
        if(self.calc_config.unit == "mg"):
            threshold = 90
            glucose_values = self.df[GLUCOSE] / 18

        if(self.calc_config.unit == "mmol"):
            threshold = 90 / 18
            glucose_values = self.df[GLUCOSE]


        GRADEs = 425 * np.power(np.log10(np.log10(np.ma.array(glucose_values)) + 0.16), 2)
        hypoglycemias = glucose_values < threshold

        return np.nansum(GRADEs[hypoglycemias]) / np.nansum(GRADEs)


class GVgrade_hyper(GVIndex):
    def __init__(self, **kwargs):
        super(GVgrade_hyper, self).__init__(**kwargs)

    def calculate(self):
        if(self.calc_config.unit == "mg"):
            threshold = 140
            glucose_values = self.df[GLUCOSE] / 18

        if(self.calc_config.unit == "mmol"):
            threshold = 140 / 18
            glucose_values = self.df[GLUCOSE]


        GRADEs = 425 * np.power(np.log10(np.log10(np.ma.array(glucose_values)) + 0.16), 2)
        hyperglycemias = glucose_values > threshold

        return np.nansum(GRADEs[hyperglycemias]) / np.nansum(GRADEs)
            

class GVlbgi(GVIndex):
    def __init__(self, **kwargs):
        super(GVlbgi, self).__init__(**kwargs)

    def calculate(self):
        f_glucose = 1.509 * (np.power(np.log10(np.ma.array(self.df[GLUCOSE])), 1.084) - 5.381)
        r_glucose = 10 * np.power(f_glucose, 2)

        rl = np.array(r_glucose)
        rl[f_glucose > 0] = 0

        return np.nanmean(rl)


class GVhbgi(GVIndex):
    def __init__(self, **kwargs):
        super(GVhbgi, self).__init__(**kwargs)

    def calculate(self):
        f_glucose = 1.509 * (np.power(np.log10(np.ma.array(self.df[GLUCOSE])), 1.084) - 5.381)
        r_glucose = 10 * np.power(f_glucose, 2)

        rh = np.array(r_glucose)
        rh[f_glucose < 0] = 0

        return np.nanmean(rh)


class GVeA1c(GVIndex):
    def __init__(self, **kwargs):
        super(GVeA1c, self).__init__(**kwargs)

    def calculate(self):
        if(self.calc_config.unit == "mg"):
            glucose_values = self.df[GLUCOSE] / 18.02
        
        if(self.calc_config.unit == "mmol"):
            glucose_values = self.df[GLUCOSE]

        return (np.nanmean(glucose_values) + 2.52) / 1.583


class GVauc(GVIndex):
    """Calculates AUC under the glucose curve.

    It uses the trapezoid rule via numpy.trapz
    Before the actual calculation, nan values are replaced
    with 0s. The final result is normalized to interval and 
    length of the measurement (supplied via calc_config)

    """
    def __init__(self, **kwargs):
        super(GVauc, self).__init__(**kwargs)

    def calculate(self):
        # nan replacement is required for the auc functions
        glucose_values = np.where(self.df[GLUCOSE] == np.nan, 0, self.df[GLUCOSE])

        return np.trapz(glucose_values, dx=self.calc_config.interval)   \
            / self.calc_config.interval / len(glucose_values)


class GVhypo_events_count(GVIndex):
    def __init__(self, **kwargs):
        super(GVhypo_events_count, self).__init__(**kwargs)

    def calculate(self, threshold: int, hypo_event_records_threshold_duration: int = 15):
        """Calculates number of hypoglycemic events.

        Arguments:
            threshold (int):
                Values of glycemia below this are treated as hypoglycemias
            hypo_event_records_threshold_duration (int):
                Sequence of hypoglycemic glucose values must have duration
                greater than this to be counted as a hypoglycemic event.
                Value is expressed in minutes. Default = 15

        Returns:
            int:
                number of hypoglycemic events
        
        Raises:
            ValueError:
                if threshold or hypo_event_records_threshold_duration
                are not int

        """
        if(type(threshold) != int):
            raise ValueError("threshold must be int")

        hypoglycemias = self.df[GLUCOSE] < threshold

        hypo_event_records_threshold = hypo_event_records_threshold_duration / self.calc_config.interval

        current_hypo_records = 0
        total_hypo_event_count = 0
        for record in hypoglycemias:
            if(record):
                current_hypo_records = current_hypo_records + 1
            else:
                if(current_hypo_records > hypo_event_records_threshold):
                    total_hypo_event_count = total_hypo_event_count + 1
                current_hypo_records = 0

        return total_hypo_event_count


class GVtime_in_hypo(GVIndex):
    def __init__(self, **kwargs):
        super(GVtime_in_hypo, self).__init__(**kwargs)

    def calculate(self, threshold: int):
        if(type(threshold) != int):
            raise ValueError("threshold must be int")

        hypoglycemias = self.df[GLUCOSE] < threshold

        return np.nansum(hypoglycemias) * self.calc_config.interval


class GVmean_hypo_event_duration(GVIndex):
    """Calculates mean duration of hypoglycemic events.

    Hypoglycemic event is defined as a sequence of hypoglycemic
    glucose values.

    """
    def __init__(self, **kwargs):
        super(GVmean_hypo_event_duration, self).__init__(**kwargs)

    def calculate(self, threshold: int, hypo_event_records_threshold_duration: int = 15):
        """Calculates mean duration of hypoglycemic events.

        Arguments:
            threshold (int):
                Values of glycemia below this are treated as hypoglycemias
            hypo_event_records_threshold_duration (int):
                Sequence of hypoglycemic glucose values must have duration
                greater than this to be counted as a hypoglycemic event.
                Value is expressed in minutes. Default = 15

        Returns:
            float:
                mean duration of hypoglycemic events
        
        Raises:
            ValueError:
                if threshold or hypo_event_records_threshold_duration
                are not int

        """
        if(type(threshold) != int):
            raise ValueError("threshold must be int")

        if(type(hypo_event_records_threshold_duration) != int):
            raise ValueError("hypo_event_records_threshold_duration must be an int")

        hypoglycemias = self.df[GLUCOSE] < threshold

        hypo_event_records_threshold = hypo_event_records_threshold_duration / self.calc_config.interval

        current_hypo_records = 0
        total_hypo_event_count = 0
        hypo_events_duration = []
        for record in hypoglycemias:
            if(record):
                current_hypo_records = current_hypo_records + 1
            else:
                if(current_hypo_records > hypo_event_records_threshold):
                    total_hypo_event_count = total_hypo_event_count + 1
                    hypo_events_duration.append(current_hypo_records)
                current_hypo_records = 0

        return np.nanmean(hypo_events_duration) * self.calc_config.interval


INDICES_TO_CALC = {
    "Mean" : GVMean,
    "Median" : GVMedian,
    "Variance" : GVVariance,
    "CV" : GVCV,
    "Missing values" : GVNanFraction,
    "Total time points No" : GVRecordsNo
}