import "./ChoiceOverlay.css";

// onChoose function is brought from the GamePage
function ChoiceOverlay({onChoose}) {

  const words = ["Apple", "Rocket", "Dragon"];

  /* this will eventually be chosen randomly from 
  a set of stored words */  

  return (
    <div className="choice-overlay">
      <h2>Choose a word</h2>

      <div className="word-buttons">


        {words.map((word) => (
          <button 
              key={word}
              onClick={onChoose}
          >

            {word}
          </button>
        ))}

        {/* goes through the list "words" and takes each
        word stores it into "word" and assigns a button 
        for each */}


      </div>
    </div>
  );
}

export default ChooseWordOverlay;