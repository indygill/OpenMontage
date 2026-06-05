/* Sample state — lets index.html render with no server / no projects on disk.
   The real /api/state (server.py) returns the same shape from projects/ + pipelines/. */
(function(){
  // mk(names, currentIndex, currentState) -> [{name,status}]
  function mk(names, cur, curState){
    return names.map((n,i)=>({name:n, status: i<cur?'done' : i===cur?curState : 'pending'}));
  }
  const NF=['concept','proposal','characters','story','script','breakdown','scene_plan','assets','edit','compose','publish'];
  const GEN=['research','proposal','script','scene_plan','assets','edit','compose','publish'];

  window.SAMPLE_STATE={
    generated_at:'sample',
    projects:[
      {
        name:'the-lighthouse-keeper', title:'The Lighthouse Keeper', pipeline:'narrative-film',
        status:'awaiting', cost:'$0.38', updated:'2m ago', stageLabel:'scene_plan', dur:'4:00',
        thumb:['#2a2236','#0c0a12'], stages:mk(NF,6,'needs'),
        gate:{ stage:'scene_plan', title:'Shot list awaiting your approval',
          message:'Shot list awaiting your approval — 14 shots',
          meta:'14 shots · 3 sequences · 4:00 runtime',
          reviewer:'Reviewer: 2 suggestions · 0 critical',
          findings:['Shots 4–6 reuse the same wide framing — vary the shot size for rhythm.',
                    'Hero shot (SH 9) has no lighting_key set — specify for predictable output.'] },
        detail:{
          format:'short film · 2.39:1 · 4:00', stageCaption:'Stage 7 of 11 · scene_plan · shot list',
          budget:{used:'$0.38',total:'$2.00',pct:19},
          shots:[['#2a2236','#0c0a12'],['#26303a','#0a0d10'],['#2a2014','#0c0a06'],['#222a2a','#0a0c0c'],['#301f26','#0c0608'],['#1e2a30','#080a0d']],
          artifacts:[['story_bible','done'],['cast','done'],['story','done'],['script','done'],['locations','done'],
                     ['sequence_plan','done'],['scene_plan','needs'],['asset_manifest','pending'],['edit_decisions','pending'],['render_report','pending']]
                     .map(([name,status])=>({name,status})),
          facts:{'Render runtime':'Remotion','Style playbook':'clean-professional','Format':'2.39:1 · 2160p','Created':'3 days ago'},
          decision:{id:'render_runtime_selection', why:'Remotion — React scene stack fits the shot list',
            options:'options: remotion · hyperframes · ffmpeg'} }
      },
      {name:'northwind-promo', title:'Northwind Promo', pipeline:'brand-narrative', status:'running',
        cost:'$0.21', updated:'now', stageLabel:'assets', dur:'0:15', thumb:['#2a2010','#0c0a06'], stages:mk(GEN,4,'running')},
      {name:'signal-from-tomorrow', title:'SIGNAL FROM TOMORROW', pipeline:'cinematic', status:'running',
        cost:'$1.92', updated:'4m ago', stageLabel:'compose', dur:'1:30', thumb:['#2a1a16','#0c0706'], stages:mk(GEN,6,'running')},
      {name:'the-last-banana', title:'The Last Banana', pipeline:'animation', status:'done',
        cost:'$1.33', updated:'1h ago', stageLabel:'published', dur:'1:00', thumb:['#2a2614','#0c0b06'], stages:mk(GEN,8,'done')},
      {name:'void-neural-interface', title:'VOID — Neural Interface', pipeline:'brand-narrative', status:'done',
        cost:'$0.69', updated:'3h ago', stageLabel:'published', dur:'0:30', thumb:['#10202e','#06090c'], stages:mk(GEN,8,'done')},
      {name:'into-the-abyss', title:'Into the Abyss', pipeline:'animation', status:'done',
        cost:'$0.15', updated:'1d ago', stageLabel:'published', dur:'0:45', thumb:['#0e2630','#060a0c'], stages:mk(GEN,8,'done')},
      {name:'quantum-computing-101', title:'Quantum Computing 101', pipeline:'animated-explainer', status:'failed',
        cost:'$0.40', updated:'2d ago', stageLabel:'assets — failed', dur:'2:00', thumb:['#2a1414','#0c0606'], stages:mk(GEN,4,'failed')},
    ]
  };
})();
