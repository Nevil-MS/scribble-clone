import { useState } from "react"
import "./styles/KeybindInput.css"

function KeybindInput({label, defaultKey}) {

    const [key, setKey] = useState(defaultKey)

    function captureKey(event){
        setKey(event.key.toUpperCase())
    }

    return(
        <div>
            <label>{label}</label><br />
            <input 
                value={key}
                onKeyDown={captureKey} 
                readOnly 
            />
        </div>
    )
}

export default KeybindInput