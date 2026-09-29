const research_form = document.getElementById('research')
const submitBtn = document.getElementById('submit_btn')

function formSubmitCatch(){
    let fields = research_form.elements
    let queryInfo = [fields[0].value, fields[1].value, fields[2].value]
    let strQuery = JSON.stringify(queryInfo)
    localStorage.setItem('query', strQuery)
    console.log("la fonction entre")
    window.location.href = window.location.href + "recherche"
}


window.addEventListener('load', function(){
    console.log('base load')
    research_form.addEventListener('submit', function(event){event.preventDefault(); formSubmitCatch()})
})
