//uso jquery

//impostazione di una funzione sul documento
$(document).ready(function(){
    //nel caso un elemento con la classe ".btn-close" venisse cliccato
    $(".btn-close").click(function(){
        //l'alert viene nascosto
        $(".alert").hide();
    });
});