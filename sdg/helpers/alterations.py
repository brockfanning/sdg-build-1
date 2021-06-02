import pandas as pd

def alter_data(alterations, data, indicator_id=None, indicator_name=None, meta=None):
    """Perform any alterations on some data.

    Parameters
    ---------
    data : DataFrame or None
    """
    # If empty or None, do nothing.
    if data is None or not isinstance(data, pd.DataFrame) or data.empty:
        return data
    # Apply any mappings.
    data = self.apply_column_map(data)
    data = self.apply_code_map(data)
    # Perform any alterations on the data.
    for alteration in alterations:
        try:
            data = alteration(data, {
                'indicator_id': indicator_id,
                'indicator_name': indicator_name,
                'meta': meta
            })
        except:
            # Handle callbacks without the context parameter.
            data = alteration(data)
    if data is None:
        raise Exception('Data alteration functions should return the altered dataframe.')
    # Always do these hardcoded steps.
    data = self.fix_dataframe_columns(data)
    data = self.fix_empty_values(data)

    return data


def alter_meta(alterations, meta, indicator_id=None, indicator_name=None, data=None):
    """Perform any alterations on some metadata.

    Parameters
    ---------
    meta : dict or None
    """
    if not meta or meta is None:
        if len(alterations) > 0:
            meta = {}
        else:
            return meta
    for alteration in alterations:
        try:
            meta = alteration(meta, {
                'indicator_id': indicator_id,
                'indicator_name': indicator_name,
                'data': data
            })
        except:
            # Handle callbacks without the context parameter.
            meta = alteration(meta)
    if meta is None:
        raise Exception('Metadata alteration functions should return the altered dict.')
    return meta


def alter_indicator_id(alterations, indicator_id, indicator_name=None, data=None, meta=None):
    """Alter an indicator id (1-1-1, 1-2-1, etc).

    Parameters
    ----------
    indicator_id : string
        The raw indicator ID
    """
    # Perform any alterations on the indicator id.
    if len(alterations) > 0:
        for alteration in alterations:
            try:
                indicator_id = alteration(indicator_id, {
                    'indicator_name': indicator_name,
                    'data': data,
                    'meta': meta
                })
            except:
                # Handle callbacks without the context parameter.
                indicator_id = alteration(indicator_id)
    # Always make sure that dots are replaced with dashes.
    indicator_id = indicator_id.replace('.', '-')
    return indicator_id


def alter_indicator_name(alterations, indicator_name, indicator_id, data=None, meta=None):
    """Alter an indicator name.

    Parameters
    ----------
    indicator_name : string
        The raw indicator name
    indicator_id : string
        The indicator id (eg, 1.1.1, 1-1-1, etc.) for this indicator
    """
    # Perform any alterations on the indicator id.
    if len(alterations) > 0:
        for alteration in alterations:
            try:
                indicator_name = alteration(indicator_name, {
                    'indicator_id': indicator_id,
                    'data': data,
                    'meta': meta
                })
            except:
                # Handle callbacks without the context parameter.
                indicator_name = alteration(indicator_name)
    return indicator_name

def apply_column_map(column_map, data):
    if column_map is not None:
        column_map=pd.read_csv(column_map)
        column_dict = dict(zip(column_map['Text'], column_map['Value']))
        data.rename(columns=column_dict, inplace=True)
    return data


def apply_code_map(code_map, data):
    if code_map is not None:
        code_map=pd.read_csv(code_map)
        code_dict = {}
        for _, row in code_map.iterrows():
            if row['Dimension'] not in code_dict:
                code_dict[row['Dimension']] = {}
            code_dict[row['Dimension']][row['Text']] = row['Value']
        data.replace(to_replace=code_dict, value=None, inplace=True)
    return data
