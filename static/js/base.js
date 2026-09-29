const URLbase = "http://127.0.0.1:5000/"
const research_form = document.getElementById('research')
const submitBtn = document.getElementById('submit_btn')
submitBtn.classList.add()

function formSubmitCatch(){
    let fields = research_form.elements
    let queryInfo = [fields[0].value, fields[1].value, fields[2].value]
    console.log(`test : ${isNullOrEmpty(queryInfo[0])}`)
    if(!(isNullOrEmpty(queryInfo[0]) && isNullOrEmpty(queryInfo[1]) && isNullOrEmpty(queryInfo[2]))){
        let strQuery = JSON.stringify(queryInfo)
        localStorage.setItem('query', strQuery)
        console.log("la fonction entre")
        window.location.href = URLbase + "publications/recherche"
    }
}

function isNullOrEmpty(element){
    let str = String(element)
    let res = ((str.trim().length === 0) || (str === null) || (str.trim() === "empty"))
    return res
}

window.addEventListener('load', function(){
    console.log('base load')
    research_form.addEventListener('submit', function(event){event.preventDefault(); formSubmitCatch()})
})
