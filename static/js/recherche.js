
"use strict";
const research_form = document.getElementById('research')
const fetch_URL = "/API/publication/search"
const result_display = document.getElementById('display')
const CITY_REGEX = /^[A-Za-zÀ-ÖØ-öø-ÿ\s\-'.]{2,85}$/;
const filters_btn = document.querySelectorAll('.btn-filter')

let last_query_results = []

let valid_start = false;
let valid_end = false;



function displayAsResult(items){
    clearDisplay()
    if(items.length > 0)
    {
        for(let i = 0; i < items.length; i++)
        {
            result_display.appendChild(createListItem(items[i]));
        }
    }
    else
    {
        let message = document.createElement('p')
        message.innerHTML = 'Aucun résultat'
        result_display.appendChild(message)
    }
}

function clearDisplay(){
    console.log("nettoyage de la liste");
    result_display.innerHTML = ''
}


function sortResults(items, filter){
    if (filter === "tous"){return items}

    let sorted = []
    console.log(items)
    for(const item of items){
        console.log(item)
        if(item['location'] === filter){
            
            sorted.push(item)
        }
    }
    // console.log(sorted)
    return sorted
}
    
async function formSubmitCatch(){
    // if(formInputValidation(research_form)){
    //     let result = await fetchFromResearch()
    //     displayAsResult(result)
    // }
    let inputs_values = [research_form.elements[0].value, research_form.elements[1].value, research_form.elements[2].value]
    if(formInputValidation(inputs_values)){
        last_query_results = await fetchFromResearch(inputs_values)
        console.log(last_query_results)
        displayAsResult(last_query_results)
    }
}   

function filterClickCatch(self){
    for(let  i = 0 ; i <filters_btn.length; i++){
        filters_btn[i].classList.remove('active')
    }
    self.classList.add('active')
    console.log(typeof self)
    let value = self.value
    displayAsResult(sortResults(last_query_results, value))
    console.log(`le bouton ${self.innerHTML} a été cliqué`)
}
    
async function fetchFromResearch(query){
    let params = {'city':String(query[0]), 'start':query[1], 'end':query[2]}
    let publications = await envoyerRequeteAjax(fetch_URL, 'GET', params)
    console.log(publications.length)
    return publications
}

function formInputValidation(fields){
    let valid1 = false;

    
    let one_input_filled = (!isNullOrEmpty(fields[0]) | !isNullOrEmpty(fields[1]) | !isNullOrEmpty(fields[2]));

    let valid_inputs;


    if(CITY_REGEX.test(fields[0])){
        valid1 = true
    }
    else if(isNullOrEmpty(fields[0])){
        valid1 = true
        fields[0] = 'empt'
    }
    else{
        valid1=false
    }

    
    if(isNullOrEmpty(fields[1])){
        valid_start = true
        fields[1] = Date.parse("1970-01-01")
    }
    else{
        valid_start=true
        fields[1] = Date.parse(fields[1])
    }

    if(Date.parse(fields[2]) < Date.parse(fields[1]) ){
        valid_end = false
    }
    else if(Date.parse(fields[2]) < Date.parse(fields[1]) || isNullOrEmpty(fields[2])){
        valid_end = true
        fields[2] = Date.parse("3000-01-01")
    }
    else{
        valid_end = true
        fields[2] = Date.parse(fields[2])
    }

    valid_inputs = (valid1 & valid_start & valid_end)


    return (one_input_filled & valid_inputs)
}

function createListItem(item){
    let item_container = document.createElement('li');
    item_container.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');

    let container_div = document.createElement('div');
    container_div.classList.add('container');

    let container_row_div = document.createElement('div');
    container_row_div.classList.add('row', 'gap-2');

    let item_img = document.createElement('img');
    item_img.src = item['img'] === null ? '../../static/img/placeholder.jpg': item['img'];
    item_img.classList.add('col-2');    

    let item_info_container = document.createElement('div');
    item_info_container.classList.add('col');

    let item_info_address = document.createElement('p');
    item_info_address.innerHTML = item['address'];

    let item_info_emplacement = document.createElement('span');
    item_info_emplacement.classList.add('badge', 'rounded-3', 'bg-dark');
    item_info_emplacement.innerHTML = item['location'] === null ? 'location null': item['location']

    let item_info_price = document.createElement('span');
    item_info_price.innerHTML =  item['price'] === null ? '22': item['price']

    // Assemblage des pièces
    item_info_container.append(item_info_address, item_info_emplacement)

    container_row_div.append(item_img, item_info_container)
    container_div.append(container_row_div)

    item_container.append(container_div, item_info_price)
    return item_container
}

function isNullOrEmpty(element){
    let str = String(element)
    let res = ((str.trim().length === 0) || (str === null) || (str.trim() === "empty"))
    return res
}


function init(){
    console.clear();
    research_form.addEventListener('submit', function(event){
        event.preventDefault();
        formSubmitCatch();
    })

    for(const btn of filters_btn){
        // console.log(i)
        btn.addEventListener('click', () => {
            filterClickCatch(btn)
        })
    }

}
window.addEventListener('load', init())
