async page => {
  const editor=page.getByRole('textbox',{name:'Student Arduino exercises'});
  await editor.fill((await editor.inputValue())+'\n// Edit after passing: require a new simulation.\n');
}
