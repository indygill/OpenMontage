/* Sample state — lets index.html render with no server / no projects on disk.
   The real /api/state (server.py) returns the same shape from projects/ + pipelines/. */
(function(){
  function mk(names, cur, curState){
    return names.map((n,i)=>({name:n, status: i<cur?'done' : i===cur?curState : 'pending'}));
  }
  const NF=['concept','proposal','characters','story','script','breakdown','scene_plan','assets','edit','compose','publish'];
  const GEN=['research','proposal','script','scene_plan','assets','edit','compose','publish'];

  const SHOTS=[
    {n:1,seq:'Arrival',desc:'Supply boat pulls away; Thomas alone on the jetty.',lang:['WIDE','24mm','overcast','static'],dur:'0:14',thumb:['#26303a','#0a0d10']},
    {n:2,seq:'Arrival',desc:'Thomas hauls his trunk up the rocks toward the tower.',lang:['MEDIUM','35mm','natural','tracking'],dur:'0:11',thumb:['#2a2620','#0c0a06']},
    {n:3,seq:'Arrival',desc:'Close on weathered hands turning the great iron key.',lang:['CLOSE','85mm','low-key','static'],dur:'0:08',thumb:['#241c14','#0a0806']},
    {n:4,seq:'The Light',desc:'The lamp room — the lens revolves, throwing long beams.',lang:['WIDE','24mm','volumetric','dolly-in'],dur:'0:16',thumb:['#2a2236','#0a0810']},
    {n:5,seq:'The Light',desc:'Thomas climbs the spiral stair, lamp glow above.',lang:['MED-WIDE','35mm','rim-lit','crane-up'],dur:'0:13',thumb:['#1e2630','#080a0d']},
    {n:6,seq:'The Light',desc:'Insert: the logbook, a single unfamiliar entry.',lang:['INSERT','100mm','tungsten','static'],dur:'0:07',thumb:['#2a201a','#0c0906']},
    {n:7,seq:'The Sea',desc:'Storm builds; waves hammer the base of the tower.',lang:['XWIDE','14mm','blue-hour','static'],dur:'0:15',thumb:['#10202e','#06090c']},
    {n:8,seq:'The Sea',desc:'Thomas at the window, lit by the turning beam.',lang:['MEDIUM','50mm','silhouette','push-in'],dur:'0:12',thumb:['#241a26','#0a0810']},
  ];
  const VOID_ASSETS=[
    {type:'IMG',kind:'img',file:'scene_01_hero.png',tool:'gpt-image-1',prov:'generated',thumb:['#10243a','#06090d']},
    {type:'IMG',kind:'img',file:'scene_02_node.png',tool:'gpt-image-1',prov:'generated',thumb:['#1a1030','#08060c']},
    {type:'IMG',kind:'img',file:'scene_03_grid.png',tool:'gpt-image-1',prov:'generated',thumb:['#10302a','#06080c']},
    {type:'IMG',kind:'img',file:'scene_04_cta.png',tool:'gpt-image-1',prov:'generated',thumb:['#2a1020','#0c0608']},
    {type:'VO',kind:'wave',file:'narration_full.mp3',tool:'openai-tts',prov:'generated',wc:'#4DA3FF'},
    {type:'MUS',kind:'wave',file:'bed_ambient.mp3',tool:'pixabay',prov:'stock',wc:'#646b78'},
    {type:'SRT',kind:'img',file:'subtitles.srt',tool:'whisperx',prov:'generated',thumb:['#15171c','#0c0e12']},
    {type:'VID',kind:'img',file:'final.mp4',tool:'remotion',prov:'provided',thumb:['#10243a','#06090d']},
  ];
  const LH_ACTIVITY=[
    {time:'now',type:'gate',main:'⏸  Paused — scene_plan awaiting your approval',sub:'Checkpoint written. Waiting for you in the agent session.'},
    {time:'0:04',type:'cp',main:'wrote checkpoint_scene_plan.json',sub:'status: awaiting_human · artifact validated ✓'},
    {time:'0:04',type:'skill',main:'Self-review · 2 suggestions, 0 critical',sub:'reviewer.md · within tolerance, proceeding to checkpoint'},
    {time:'0:09',type:'tool',main:'scene_plan → 14 shots across 3 sequences',sub:'built from script.json · resolved cast + location ids ✓'},
    {time:'0:21',type:'skill',main:'Read scene-director skill',sub:'skills/pipelines/narrative-film/scene-director.md'},
    {time:'0:22',type:'cp',main:'wrote checkpoint_breakdown.json',sub:'status: completed · locations + sequence_plan derived'},
    {time:'0:48',type:'paid',main:'Announced: 0 paid calls this stage',sub:'breakdown is deterministic — no provider spend'},
    {time:'1:30',type:'note',main:'Resumed project · entry stage = script',sub:'provided script.fdx ingested (locked) · derived upstream'},
  ];
  const VOID_COST={budget:{used:'$0.69',total:'$2.00',pct:34},note:'34% of budget · estimate was $0.74 · reconciled −$0.05',
    items:[{tool:'image_generation',prov:'gpt-image-1',qty:'4',cost:'$0.32'},{tool:'tts',prov:'openai-tts',qty:'1',cost:'$0.11'},
      {tool:'music',prov:'pixabay',qty:'1',cost:'$0.00'},{tool:'subtitles',prov:'whisperx (local)',qty:'1',cost:'$0.00'},
      {tool:'compose',prov:'remotion (local)',qty:'3',cost:'$0.00'}],total:'$0.69',
    decisions:[{id:'render_runtime_selection',when:'proposal',why:'Remotion — React scene stack + data viz fit the brand explainer.',options:'options: remotion · hyperframes · ffmpeg'},
      {id:'image_provider',when:'assets',why:'Only OpenAI key configured; single-key production.',options:'options: gpt-image-1 · flux · imagen'}]};

  window.SAMPLE_STATE={
    generated_at:'sample',
    projects:[
      {
        name:'the-lighthouse-keeper', title:'The Lighthouse Keeper', pipeline:'narrative-film',
        status:'awaiting', cost:'$0.38', updated:'2m ago', stageLabel:'scene_plan', dur:'4:00',
        thumb:['#2a2236','#0c0a12'], stages:mk(NF,6,'needs'),
        gate:{ stage:'scene_plan', title:'Shot list awaiting your approval',
          message:'Shot list awaiting your approval — 14 shots',
          meta:'14 shots · 3 sequences · 4:00 runtime', reviewer:'Reviewer: 2 suggestions · 0 critical',
          findings:['Shots 4–6 reuse the same wide framing — vary the shot size for rhythm.',
                    'Hero shot (SH 9) has no lighting_key set — specify for predictable output.'] },
        detail:{
          format:'short film · 2.39:1 · 4:00', stageCaption:'Stage 7 of 11 · scene_plan · shot list',
          budget:{used:'$0.38',total:'$2.00',pct:19},
          shots:[['#2a2236','#0c0a12'],['#26303a','#0a0d10'],['#2a2014','#0c0a06'],['#222a2a','#0a0c0c'],['#301f26','#0c0608'],['#1e2a30','#080a0d']],
          shotList:SHOTS, activity:LH_ACTIVITY,
          artifacts:[['story_bible','done'],['cast','done'],['story','done'],['script','done'],['locations','done'],
                     ['sequence_plan','done'],['scene_plan','needs'],['asset_manifest','pending'],['edit_decisions','pending'],['render_report','pending']].map(([name,status])=>({name,status})),
          facts:{'Render runtime':'Remotion','Style playbook':'clean-professional','Format':'2.39:1 · 2160p','Created':'3 days ago'},
          decision:{id:'render_runtime_selection',why:'Remotion — React scene stack fits the shot list',options:'options: remotion · hyperframes · ffmpeg'},
          cost:{budget:{used:'$0.38',total:'$2.00',pct:19},note:'19% of budget · 4 image gens + narration pending',
            items:[{tool:'image_generation',prov:'flux (planned)',qty:'14',cost:'$0.38'},{tool:'breakdown',prov:'local',qty:'1',cost:'$0.00'}],total:'$0.38',
            decisions:[{id:'render_runtime_selection',when:'proposal',why:'Remotion fits the shot list.',options:'options: remotion · hyperframes · ffmpeg'}]} }
      },
      {name:'northwind-promo', title:'Northwind Promo', pipeline:'brand-narrative', status:'running',
        cost:'$0.21', updated:'now', stageLabel:'assets', dur:'0:15', thumb:['#2a2010','#0c0a06'], stages:mk(GEN,4,'running')},
      {name:'signal-from-tomorrow', title:'SIGNAL FROM TOMORROW', pipeline:'cinematic', status:'running',
        cost:'$1.92', updated:'4m ago', stageLabel:'compose', dur:'1:30', thumb:['#2a1a16','#0c0706'], stages:mk(GEN,6,'running')},
      {name:'the-last-banana', title:'The Last Banana', pipeline:'animation', status:'done',
        cost:'$1.33', updated:'1h ago', stageLabel:'published', dur:'1:00', thumb:['#2a2614','#0c0b06'], stages:mk(GEN,8,'done')},
      {name:'void-neural-interface', title:'VOID — Neural Interface', pipeline:'brand-narrative', status:'done',
        cost:'$0.69', updated:'3h ago', stageLabel:'published', dur:'0:30', thumb:['#10202e','#06090c'], stages:mk(GEN,8,'done'),
        detail:{
          format:'product ad · 16:9 · 0:30', budget:{used:'$0.69',total:'$2.00',pct:34},
          assets:VOID_ASSETS, cost:VOID_COST,
          artifacts:[['brief','done'],['script','done'],['scene_plan','done'],['asset_manifest','done'],['edit_decisions','done'],['render_report','done']].map(([name,status])=>({name,status})),
          facts:{'Render runtime':'Remotion','Format':'16:9 · 1080p','Created':'today'},
          decision:{id:'render_runtime_selection',why:'Remotion — data viz + word-level captions',options:'options: remotion · hyperframes · ffmpeg'},
          render:{dur:'0:30',
            variants:[{label:'Master',sub:'16:9 · 1920×1080'},{label:'Reel',sub:'9:16 · 1080×1920'},{label:'Square',sub:'1:1 · 1080×1080'}],
            outputs:[{role:'hero',aspect:'Master 16:9',res:'1920×1080',size:'18.4 MB'},
              {role:'derivative',aspect:'Reel 9:16',res:'1080×1920',size:'9.1 MB'},
              {role:'derivative',aspect:'Square 1:1',res:'1080×1080',size:'7.7 MB'}],
            facts:'renders/final.mp4   ·   h264 · 1920×1080 · 24fps · 0:30 · 18.4 MB   ·   ✓ ffprobe verified',
            facts2:{Runtime:'Remotion','Render time':'41s',Encoding:'h264 · aac',Subtitles:'WhisperX · burned'}} }},
      {name:'into-the-abyss', title:'Into the Abyss', pipeline:'animation', status:'done',
        cost:'$0.15', updated:'1d ago', stageLabel:'published', dur:'0:45', thumb:['#0e2630','#060a0c'], stages:mk(GEN,8,'done')},
      {name:'quantum-computing-101', title:'Quantum Computing 101', pipeline:'animated-explainer', status:'failed',
        cost:'$0.40', updated:'2d ago', stageLabel:'assets — failed', dur:'2:00', thumb:['#2a1414','#0c0606'], stages:mk(GEN,4,'failed')},
    ],
    inbox:{
      needs:[
        {state:'needs',name:'the-lighthouse-keeper',title:'The Lighthouse Keeper',pipeline:'narrative-film',message:'Shot list awaiting your approval — 14 shots',time:'2m ago'},
        {state:'needs',name:'northwind-promo',title:'Northwind Spring Drop',pipeline:'brand-narrative',message:'Proposal ready — confirm runtime & budget',time:'18m ago'}],
      recent:[
        {state:'done',name:'void-neural-interface',title:'VOID — Neural Interface',pipeline:'brand-narrative',message:'Render complete · 3 outputs (16:9 / 9:16 / 1:1)',time:'3h ago'},
        {state:'failed',name:'quantum-computing-101',title:'Quantum Computing 101',pipeline:'animated-explainer',message:'assets stage failed — FLUX provider returned 429',time:'2d ago'},
        {state:'running',name:'signal-from-tomorrow',title:'SIGNAL FROM TOMORROW',pipeline:'cinematic',message:'Compose started · rendering via Remotion',time:'4m ago'},
        {state:'done',name:'the-last-banana',title:'The Last Banana',pipeline:'animation',message:'Published · exported with metadata',time:'1d ago'}]
    },
    capabilities:{
      runtimes:[{name:'FFmpeg',note:'always available'},{name:'Remotion',note:'npx + node_modules ready'},{name:'HyperFrames',warn:true,note:'npm package not resolvable'}],
      rows:[
        {name:'Video generation',conf:0,total:13,provs:['—']},
        {name:'Image generation',conf:1,total:7,provs:['gpt-image-1']},
        {name:'Text-to-speech',conf:1,total:3,provs:['openai-tts']},
        {name:'Music generation',conf:1,total:1,provs:['pixabay']},
        {name:'Composition',conf:3,total:3,provs:['ffmpeg','remotion','video_stitch']}],
      setup:[{env:'FAL_KEY',unlocks:'unlocks 6 video + 3 image providers'},
        {env:'ELEVENLABS_API_KEY',unlocks:'unlocks premium TTS + music'},
        {env:'REPLICATE_API_TOKEN',unlocks:'unlocks 4 video providers'}]
    }
  };
})();
