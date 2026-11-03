
const $ = (id) => document.getElementById(id);

let latestResult = null;
let currentPatient = null;

// PAGE NAVIGATION

function showPage(pageName) {

    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active-page");
    });

    const page = $(pageName);

    if (page) {
        page.classList.add("active-page");
    }

    document.querySelectorAll(".nav-link[data-page]").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.page === pageName
        );
    });
}

// SIDEBAR NAVIGATION

document.querySelectorAll(".nav-link[data-page]").forEach(button => {

    button.addEventListener("click", () => {
        showPage(button.dataset.page);
    });

});

// QUICK ACTION BUTTONS

document.querySelectorAll("[data-go]").forEach(button => {

    button.addEventListener("click", () => {
        showPage(button.dataset.go);
    });

});

// COLLAPSE SIDEBAR

$("menuToggle").addEventListener("click", () => {

    $("app").classList.toggle("collapsed");

});


// PATIENT REGISTRATION

$("patientForm").addEventListener("submit", event => {

    event.preventDefault();

    currentPatient = {

        name: $("fullName").value.trim(),

        gender: $("gender").value,

        age: $("age").value,

        contact: $("contact").value.trim()

    };

    $("registerMessage").textContent =
        "Patient registered successfully.";

    $("totalPatients").textContent =
        Number($("totalPatients").textContent) + 1;

    $("patientForm").reset();

});


// BLOOD SMEAR IMAGE UPLOAD

$("bloodImage").addEventListener("change", event => {

    const file = event.target.files[0];

    const preview = $("imagePreview");

    if (!file) {

        preview.style.display = "none";

        return;

    }

    if (!["image/png", "image/jpeg"].includes(file.type)) {

        alert("Please choose a PNG or JPG image.");

        event.target.value = "";

        return;

    }

    preview.src = URL.createObjectURL(file);

    preview.style.display = "block";

});


// MALARIA DIAGNOSIS DEMONSTRATION

$("diagnosisForm").addEventListener("submit", event => {

    event.preventDefault();

    const symptoms = [
        ...document.querySelectorAll(
            ".symptom-list input:checked"
        )
    ].map(input => input.value);


    // Demonstration rule only.
    // This is NOT a trained AI model.

    const positive = symptoms.length >= 3;

    const label = positive
        ? "Positive (demo)"
        : "Negative (demo)";


    latestResult = {

        result: label,

        positive: positive,

        symptoms: symptoms,

        patient: currentPatient,

        date: new Date().toLocaleDateString()

    };


    // DISPLAY RESULT

    $("resultTitle").textContent = label;

    $("confidence").textContent =
        "Symptoms selected: " + symptoms.length;


    if (negative) {

        $("resultExplanation").textContent =
            "Several symptoms were selected. This demonstration rule flags the entry for clinical assessment. It is not a diagnosis.";

    } else {

        $("resultExplanation").textContent =
            "Fewer than three symptoms were selected by the demonstration rule. This does not rule out malaria.";

    }


    $("resultAlert").style.background =
        positive ? "#f8d8ed" : "#d7f2e7";

    $("resultTitle").style.color =
        positive ? "#bd2038" : "#13764f";


    // UPDATE DASHBOARD STATISTICS

    $("totalAnalyses").textContent =
        Number($("totalAnalyses").textContent) + 1;


    if (positive) {

        $("positiveCases").textContent =
            Number($("positiveCases").textContent) + 1;

    } else {

        $("healthyCases").textContent =
            Number($("healthyCases").textContent) + 1;

    }


    // SAVE RESULT TO HISTORY

    addHistoryRow(latestResult);

    // OPEN RESULTS PAGE

    showPage("results");

});


// ADD PATIENT TO HISTORY TABLE

function addHistoryRow(record) {

    const body = $("historyBody");

    const row = document.createElement("tr");

    const name = record.patient?.name || "Guest patient";

    const age = record.patient?.age || "—";

    const pillClass = record.positive
        ? "positive"
        : "negative";

    const label = record.positive
        ? "Positive"
        : "Negative";


    row.innerHTML = `
        <td>${body.rows.length + 1}</td>

        <td></td>

        <td></td>

        <td>${record.date}</td>

        <td>
            <span class="pill ${pillClass}">
                ${label}
            </span>
        </td>

        <td>
            <button class="view-btn">◉ View</button>
        </td>
    `;


    row.cells[1].textContent = name;

    row.cells[2].textContent = age;


    row.querySelector("button").addEventListener("click", () => {

        $("resultTitle").textContent =
            label + " (demo)";

        $("confidence").textContent =
            "Symptoms selected: " +
            record.symptoms.join(", ");

        $("resultExplanation").textContent =
            "Historical demonstration entry. This result is not a clinical diagnosis.";

        showPage("results");

    });


    body.prepend(row);

}


// DOWNLOAD DIAGNOSIS REPORT

$("downloadReport").addEventListener("click", () => {

    if (!latestResult) {

        alert("Please run a demonstration analysis first.");

        return;

    }


    const report = [

        "MALARIA CARE - DEMONSTRATION REPORT",

        "-----------------------------------",

        "Patient: " +
        (latestResult.patient?.name || "Not specified"),

        "Age: " +
        (latestResult.patient?.age || "Not specified"),

        "Date: " + latestResult.date,

        "Demonstration result: " + latestResult.result,

        "Selected symptoms: " +
        (latestResult.symptoms.join(", ") || "None"),

        "",

        "IMPORTANT: This is a software demonstration only.",

        "It is not a medical diagnosis."

    ].join("\n");


    const blob = new Blob(
        [report],
        { type: "text/plain" }
    );

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;

    link.download = "malaria-demo-report.txt";

    link.click();

    URL.revokeObjectURL(url);

});
