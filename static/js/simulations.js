(function () {
  var list = document.getElementById('interval-list');
  var addButton = document.getElementById('add-interval');
  var template = document.getElementById('empty-interval');
  var total = document.getElementById('id_intervals-TOTAL_FORMS');
  if (!list || !addButton || !template || !total) return;

  function refreshNumbers() {
    list.querySelectorAll('[data-interval-form]').forEach(function (row, index) {
      row.querySelector('.interval-number').textContent = String(index + 1).padStart(2, '0');
      var position = row.querySelector('input[name$="-position"]');
      if (position) position.value = index + 1;
    });
  }

  addButton.addEventListener('click', function () {
    var index = Number(total.value);
    list.insertAdjacentHTML('beforeend', template.innerHTML.replaceAll('__prefix__', index));
    total.value = index + 1;
    refreshNumbers();
  });

  list.addEventListener('click', function (event) {
    var button = event.target.closest('.remove-interval');
    if (!button) return;
    var row = button.closest('[data-interval-form]');
    var deleteInput = row.querySelector('input[name$="-DELETE"]');
    var idInput = row.querySelector('input[name$="-id"]');
    if (idInput && idInput.value) {
      deleteInput.checked = true;
      row.hidden = true;
    } else {
      row.remove();
    }
    refreshNumbers();
  });

  refreshNumbers();

  var goalSearch = document.querySelector('[data-goal-search]');
  var goalSelect = document.getElementById('id_meta');
  var subjectInput = document.querySelector('[data-subject-input]');
  var subjectOptions = document.getElementById('subject-options');
  var subjectDataElement = document.getElementById('goal-subject-data');
  var goalSubjects = subjectDataElement ? JSON.parse(subjectDataElement.textContent) : {};

  function sanitizeSubject(value) {
    return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/[^A-Z0-9 ]/g, '').replace(/\s+/g, ' ').trimStart();
  }

  function refreshSubjectOptions() {
    if (!subjectOptions || !goalSelect) return;
    var subjects = goalSubjects[goalSelect.value] || [];
    subjectOptions.innerHTML = '';
    subjects.forEach(function (subject) {
      var option = document.createElement('option');
      option.value = subject;
      subjectOptions.appendChild(option);
    });
    if (subjectInput && subjects.length && subjectInput.value && !subjects.includes(subjectInput.value)) subjectInput.value = '';
  }

  if (goalSearch && goalSelect) {
    var originalOptions = Array.from(goalSelect.options).map(function (option) { return { value: option.value, text: option.text }; });
    goalSearch.addEventListener('input', function () {
      var query = goalSearch.value.toLocaleLowerCase('pt-BR').trim();
      var selected = goalSelect.value;
      goalSelect.innerHTML = '';
      originalOptions.filter(function (option) { return !query || option.text.toLocaleLowerCase('pt-BR').includes(query); }).forEach(function (option) {
        goalSelect.add(new Option(option.text, option.value, false, option.value === selected));
      });
      refreshSubjectOptions();
    });
    goalSelect.addEventListener('change', refreshSubjectOptions);
  }
  if (subjectInput) subjectInput.addEventListener('input', function () { subjectInput.value = sanitizeSubject(subjectInput.value); });
  refreshSubjectOptions();
}());
