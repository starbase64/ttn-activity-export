from sports import activity_type_keys, sport_label


def test_flat_and_wrapped_taxonomies_keep_unknown_types_and_deduplicate():
    flat=[{'typeKey':'running','parentTypeId':17},{'typeKey':'new_type','parentTypeId':17},
          {'typeKey':'running'},{'typeKey':None},{'unrelated':'ignore'}]
    assert activity_type_keys(flat)==['new_type','running']
    assert activity_type_keys({'activityTypes':flat,'parents':[{'activityTypeKey':'hiking'}]})==['hiking','new_type','running']
    assert activity_type_keys(None)==[]
    assert sport_label('hiking','de')=='Wandern (hiking)'
    assert sport_label('hiking','en')=='Hiking (hiking)'
    assert 'new_type' in sport_label('new_type','de')
