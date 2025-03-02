from flask import Flask, jsonify, request, render_template
from kombucha_simulation import KombuchaSimulation
import os

app = Flask(__name__)

# Create an instance of the simulation
simulation = KombuchaSimulation()

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/init', methods=['GET'])
def init():
    """Initialize or reset the simulation."""
    state = simulation.reset()
    return jsonify(state)

@app.route('/api/step', methods=['GET'])
def step():
    """Advance the simulation by one or more time steps."""
    steps = int(request.args.get('steps', 1))
    state = simulation.step(steps)
    return jsonify(state)

@app.route('/api/introduce', methods=['GET'])
def introduce():
    """Introduce a contaminant to the simulation."""
    contaminant_type = request.args.get('type', 'mold')
    message = simulation.introduce_contaminant(contaminant_type)
    state = simulation.get_state()
    state['message'] = message
    return jsonify(state)

@app.route('/api/state', methods=['GET'])
def get_state():
    """Get the current state of the simulation."""
    state = simulation.get_state()
    return jsonify(state)

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True)