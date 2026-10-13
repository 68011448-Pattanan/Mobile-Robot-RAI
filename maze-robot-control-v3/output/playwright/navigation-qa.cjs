async page => {
  const assert=(condition,message)=>{if(!condition)throw Error(message)};
  const errors=[]; page.on('pageerror',error=>errors.push(error.message));
  const nav=name=>page.getByRole('navigation').getByRole('button',{name,exact:true}).click();
  const button=name=>page.getByRole('button',{name,exact:true});
  await nav('Recordings');
  const select=page.getByRole('combobox',{name:'Choose recording'});
  if(await select.locator('option').count()===1){
    await button('Start recording').click();
    await page.waitForTimeout(350);
    await button('Stop & save recording').click();
  }
  await select.locator('option').nth(1).waitFor({state:'attached'});
  const recording=await select.locator('option').nth(1).textContent();
  await select.selectOption(recording);
  await button('Replay').click();
  await page.getByLabel('Replay frame').waitFor();
  await nav('Dashboard');
  await button('Start learning run').click();
  await page.waitForFunction(()=>[...document.querySelectorAll('.metric')].find(e=>e.textContent.includes('ROBOT STATE'))?.querySelector('.value')?.textContent==='SCAN');
  await button('Reset').click();
  let compiling=false;
  const delay=async route=>{compiling=true;await new Promise(resolve=>setTimeout(resolve,500));await route.continue()};
  await page.route('**/workshop/compile',delay);
  await button('Start learning run').click();
  for(let i=0;i<20&&!compiling;i++)await page.waitForTimeout(25);
  assert(compiling,'Compile request was not observed');
  await button('EMERGENCY STOP').click();
  await page.waitForTimeout(900);
  assert((await page.locator('.metric').filter({hasText:'ROBOT STATE'}).locator('.value').innerText())==='STOPPED','Pending compile restarted after Emergency Stop');
  await page.unroute('**/workshop/compile',delay);
  for(const name of ['Live discovery','Maze workspace','Maze solver','PID lab','Calibration','Path analyzer','Real robot','Serial monitor','Recordings','How it works','Firmware','Settings']){
    await nav(name);
    await page.getByRole('heading',{name,exact:true,level:1}).waitFor();
    await page.waitForTimeout(100);
  }
  await button('Simulation').click();
  await nav('Dashboard');
  await page.screenshot({path:'output/playwright/dashboard-fixed.png',fullPage:true});
  assert(errors.length===0,'Browser errors: '+errors.join('; '));
  return {passed:true,recording,checks:'Recording replay exits on new learning run; pending compile cancelled by stop; all navigation tabs render without browser exceptions.'};
}
