import React from 'react';
import DateRangePicker from '../common/date-range-picker';
import FilterField from './filter-field';
import './styles/filter.scss';


export default class RequestsFilter extends React.Component {

    constructor(props) {
        super(props);
        this.onDatePickerChange = this.onDatePickerChange.bind(this);
        this.onNameChange = this.onNameChange.bind(this);
        this.onReferenceNumberChange = this.onReferenceNumberChange.bind(this);
        this.onPostcodeChange = this.onPostcodeChange.bind(this);
        this.submit = this.submit.bind(this);

        this.state = {
            dates: {
                start: null, end: null     // TODO
            },
            name: props.name || '',
            referenceNumber: props.referenceNumber || '',
            postcode: props.postcode || ''
        };
    }

    onDatePickerChange(dates) {
        this.setState({ dates });
    }

    onNameChange(name) {
        this.setState({ name });
    }

    onReferenceNumberChange(referenceNumber) {
        this.setState({ referenceNumber });
    }

    onPostcodeChange(postcode) {
        this.setState({ postcode });
    }

    submit() {
        this.props.onSubmit({
            dates: this.state.dates,
            name: this.state.name,
            referenceNumber: this.state.referenceNumber,
            postcode: this.state.postcode
        });
    }

    render() {
        return (
            <div className="requests-filter panel">
                <label>Filters:</label>
                <DateRangePicker onChange={ this.onDatePickerChange } />
                <label className="and">and</label>
                <FilterField label="Name"
                    value={ this.state.name }
                    onChange={ this.onNameChange } />
                <FilterField label="Ref #"
                    value={ this.state.referenceNumber }
                    onChange={ this.onReferenceNumberChange } />
                <FilterField label="Postcode"
                    value={ this.state.postcode }
                    onChange={ this.onPostcodeChange } />
                <button onClick={ () => this.submit() }>Go</button>
            </div>
        );
    }
}
