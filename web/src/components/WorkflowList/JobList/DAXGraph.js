import React from 'react'
import Graph from 'reactjs-graphs'
import axios from 'axios'

const onClick = (label, index, extras) => {
    console.log(label, index, extras)
}
 
const vertices = [
    { label: "A", onClick },
    { label: "B", onClick },
    { label: "C", onClick },
    { label: "D", onClick },
    { label: "E", onClick },
    { label: "F", onClick },
    { label: "G", onClick },
    { label: "H", },
    { label: "I", },
    { label: "J", },
    { label: "K", },
    { label: "L", },
    { label: "M", },
    { label: "N", },
]
 
const edges = [
    ["A", "B"],
    ["B", "C"],
    ["C", "D"],
    ["C", "E"],
    ["C", "F"],
    ["C", "G"],
    ["F", "H"],
    ["E", "H"],
    ["G", "H"],
    ["H", "I"],
    ["H", "J"],
    ["H", "K"],
    ["K", "L"],
    ["J", "L"],
    ["I", "L"],
    ["L", "M"],
    ["L", "N"]
 ]
 
 
class DAXGraph extends React.Component{
    constructor() {
        super();
    this.state = {
       nodes:[],
       edges:[]
      }
    }
    componentDidMount() {
        axios.get('http://localhost:8000/nodes')
        .then(response => {
          this.setState({
            nodes:response.data
          });
        })
        axios.get('http://localhost:8000/edges')
        .then(response => {
          this.setState({
            edges:response.data
          });
        })
    }
  
    render(){
        return(
            <div>
            <h3>Work in Progress...This graph is an example from reactjs-graph npm module data.</h3>
    <Graph 
        vertices={vertices} 
        edges={edges} 
        width={1000} 
        height={500} 
        autoWidth={true} 
        vertexStroke="#df6766" 
        edgeStroke="#ebb2b2" 
        edgeWidth={2} 
        vertexRadius={15} 
        vertexGap={200} 
        labelFontSize={20} 
        activeVertexFill="blue" 
        inactiveVertexFill="white" 
        fontFamily="Airbnb Cereal"
        labelColor="black" 
        className="className" 
        centerInCanvas={true}
/>
</div>
)

    }
}
export default DAXGraph;