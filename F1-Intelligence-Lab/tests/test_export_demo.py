import json

import pytest

pytest.importorskip('torch')
from f1_intelligence_lab.export_demo import aggregate_payload


def test_aggregate_payload_removes_lap_and_driver_observations():
    full={
        'model_version':'abc','selected_on_2025':'tree','models':['tree','rolling_median'],
        'control_version':2,'validation':{},'regression':{},'limitations':'limited',
        'sessions':[{'id':'race-1','circuit':'Test','date':'2025-01-01','split':'validation','rows':[
            {'driver':'1','lap':12,'actual':90.0,'state':'GREEN','prediction_at':'x',
             'predictions':{'tree':91.0,'rolling_median':92.0}}
        ]}],
    }
    result=aggregate_payload(full)
    encoded=json.dumps(result).lower()
    assert result['export_mode']=='aggregate'
    assert result['races'][0]['summary']['tree']['mae_s']==1.0
    for forbidden in ['actual','driver','prediction_at','rows','lap_number','duration']:
        assert forbidden not in encoded
