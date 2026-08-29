import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const questions = [
  {
    id: "derivation",
    question: "How is your formulation derived?",
    options: [
      {
        label: "It exactly follows a classical Ayurvedic formulation",
        value: "classical",
      },
      {
        label: "It is based on tradition but has been modified",
        value: "modified",
      },
      {
        label: "It is an entirely new formulation",
        value: "new",
      },
      {
        label: "I am not sure",
        value: "unsure",
      },
    ],
  },
  {
    id: "authoritativeText",
    question:
      "Is the formulation described in an authoritative Ayurvedic text?",
    options: [
      { label: "Yes", value: "yes" },
      { label: "No", value: "no" },
      { label: "I am not sure", value: "unsure" },
    ],
  },
  {
    id: "substantiallyModified",
    question:
      "Has the formulation been substantially modified or newly developed?",
    options: [
      { label: "Yes", value: "yes" },
      { label: "No", value: "no" },
      { label: "I am not sure", value: "unsure" },
    ],
  },
  {
    id: "intendedUse",
    question: "What is the intended use of the product?",
    options: [
      { label: "Medicinal / therapeutic use", value: "medicine" },
      { label: "Food / nutraceutical use", value: "food" },
      { label: "Cosmetic use", value: "cosmetic" },
      { label: "Other / not sure", value: "other" },
    ],
  },
];

function getMockCategory(answers) {
  if (answers.intendedUse === "food") {
    return {
      title: "Ayurveda-Aahar / Nutraceutical",
      description:
        "Your product appears most aligned with an Ayurveda-Aahar or nutraceutical pathway.",
    };
  }

  if (answers.intendedUse === "cosmetic") {
    return {
      title: "Cosmetic",
      description:
        "Your product appears most aligned with the cosmetic regulatory category.",
    };
  }

  if (
    answers.derivation === "classical" &&
    answers.authoritativeText === "yes" &&
    answers.substantiallyModified === "no"
  ) {
    return {
      title: "Classical Ayurvedic Medicine",
      description:
        "Your product appears to be based on a classical formulation. Traditional-knowledge and patentability considerations will be important.",
    };
  }

  if (
    answers.derivation === "new" ||
    answers.substantiallyModified === "yes"
  ) {
    return {
      title: "New / Non-classical Drug",
      description:
        "Your product appears to include new or substantially modified elements. Safety, effectiveness, and patentability requirements may be relevant.",
    };
  }

  return {
    title: "Patent-or-Proprietary Medicine",
    description:
      "Your product appears most aligned with a patent-or-proprietary medicine pathway.",
  };
}

function Classify() {
  const navigate = useNavigate();
  const location = useLocation();

  const jurisdiction = location.state?.jurisdiction || "india";

  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);

  const currentQuestion = questions[questionIndex];
  const selectedAnswer = answers[currentQuestion.id];

  function chooseAnswer(value) {
    setAnswers((previousAnswers) => ({
      ...previousAnswers,
      [currentQuestion.id]: value,
    }));
  }

  function goNext() {
    if (questionIndex === questions.length - 1) {
      setResult(getMockCategory(answers));
      return;
    }

    setQuestionIndex((previousIndex) => previousIndex + 1);
  }

  function goBack() {
    if (questionIndex > 0) {
      setQuestionIndex((previousIndex) => previousIndex - 1);
    }
  }

  function restartClassification() {
    setQuestionIndex(0);
    setAnswers({});
    setResult(null);
  }

  if (result) {
    return (
      <div className="classification-page">
        <div className="classification-container">
          <div className="badge">CLASSIFICATION COMPLETE</div>

          <div className="result-card">
            <p className="result-label">Likely formulation category</p>
            <h1>{result.title}</h1>

            <p className="classification-intro">{result.description}</p>

            <p className="result-jurisdiction">
              Jurisdiction selected:{" "}
              <strong>
                {jurisdiction === "india" ? "India" : "International"}
              </strong>
            </p>

            <div className="disclaimer">
              <strong>Important:</strong> This is a preliminary guidance
              classification, not legal or regulatory advice.
            </div>

            <div className="navigation-buttons">
              <button className="back-button" onClick={restartClassification}>
                Start again
              </button>

              <button
  className="next-button"
  onClick={() =>
    navigate("/ask", {
      state: {
        jurisdiction,
        formulationCategory: result.title,
      },
    })
  }
>
  Continue to Ask a Question →
</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="classification-page">
      <div className="classification-container">
        <button className="text-back-button" onClick={() => navigate("/")}>
          ← Back to Home
        </button>

        <div className="badge">FORMULATION CLASSIFICATION</div>

        <h1>
          Let&apos;s understand your <span>formulation</span>
        </h1>

        <p className="classification-intro">
          Answer four short questions to identify the most relevant regulatory
          and IP guidance pathway.
        </p>

        <div className="progress-section">
          <div className="progress-text">
            Question {questionIndex + 1} of {questions.length}
          </div>

          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${((questionIndex + 1) / questions.length) * 100}%`,
              }}
            />
          </div>
        </div>

        <div className="question-card">
          <h2>{currentQuestion.question}</h2>

          <div className="options">
            {currentQuestion.options.map((option) => (
              <button
                type="button"
                key={option.value}
                className={
                  selectedAnswer === option.value ? "option selected" : "option"
                }
                onClick={() => chooseAnswer(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>

          <div className="navigation-buttons">
            <button
              className="back-button"
              onClick={goBack}
              disabled={questionIndex === 0}
            >
              ← Back
            </button>

            <button
              className="next-button"
              onClick={goNext}
              disabled={!selectedAnswer}
            >
              {questionIndex === questions.length - 1
                ? "Finish Classification"
                : "Next →"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Classify;