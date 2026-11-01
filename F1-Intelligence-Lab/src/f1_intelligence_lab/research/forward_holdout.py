"""Open a post-protocol forward holdout once, or report that it is pending."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .artifacts import finish, prepare, require_protocol_before_labels, write_json

BOUNDARY=datetime(2026,11,2,tzinfo=timezone.utc)


def opened_rows(dataset: str,output: str) -> Path:
    source=Path(dataset);source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    out=prepare(output,'forward-holdout',False,['sha256:'+source_hash])
    require_protocol_before_labels(out)
    rows: List[Dict[str,Any]]=[]
    with source.open() as handle:
        for line in handle:
            row=json.loads(line);start=datetime.fromisoformat(row['race_start'].replace('Z','+00:00'))
            if start>BOUNDARY:rows.append(row)
    races=sorted({row['session_id'] for row in rows})
    if len(races)<3:
        results={'status':'forward holdout pending','boundary':'2026-11-02','verified_races':len(races),'labels_evaluated':False}
        predictions=[]
    else:
        results={'status':'opened once','boundary':'2026-11-02','verified_races':len(races),'labels_evaluated':True,
                 'note':'Evaluation adapter must add model metrics without changing model selection.'}
        predictions=[{'session_id':row['session_id'],'row_id':row.get('row_id',''),'actual_s':row['target_s']} for row in rows]
    write_json(out/'results.json',results)
    with (out/'predictions.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['session_id','row_id','actual_s']);writer.writeheader();writer.writerows(predictions)
    with (out/'per_race.csv').open('w',newline='') as handle:
        row_writer=csv.writer(handle);row_writer.writerow(['session_id','rows'])
        for race in races:row_writer.writerow([race,sum(row['session_id']==race for row in rows)])
    (out/'REPORT.md').write_text('# Forward holdout\n\n**%s.** Boundary: races starting strictly after 2026-11-02.\n'%results['status'])
    finish(out);return out


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dataset',required=True);parser.add_argument('--output',required=True);args=parser.parse_args();opened_rows(args.dataset,args.output)


if __name__=='__main__':main()
