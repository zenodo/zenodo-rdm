import { i18next } from "@translations/invenio_communities/i18next";
import PropTypes from "prop-types";
import React, { Component } from "react";
import { withCancel, SelectField } from "react-invenio-forms";
import _debounce from "lodash/debounce";
import _truncate from "lodash/truncate";

export default class SearchDropdown extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isFetching: false,
      error: false,
      suggestions: [],
    };
  }

  optionsGenerator = (suggestions) => {
    const { serializeSuggestions } = this.props;

    return serializeSuggestions(suggestions);
  };

  onSearchChange = _debounce(async (event, { searchQuery }) => {
    const { fetchData } = this.props;

    try {
      this.setState({ isFetching: true });

      const cancellableSuggestions = withCancel(fetchData(searchQuery));
      const suggestions = await cancellableSuggestions.promise;
      this.setState({
        isFetching: false,
        suggestions: suggestions.data.hits.hits,
        error: false,
      });
    } catch (e) {
      console.error(e);
      this.setState({
        isFetching: false,
        error: true,
      });
    }
    // eslint-disable-next-line react/destructuring-assignment
  }, this.props.debounceTime);


  handleAddItem = (event, { value }) => {
    const { onAddItem } = this.props;
    if (onAddItem) {
      onAddItem(value);
    }
  };

  render() {
    const { isFetching, error } = this.state;
    const { placeholder, selectedSuggestion, fieldPath, ...uiProps } = this.props;
    const { suggestions } = this.state;

    return (
      <SelectField
        fieldPath={fieldPath}
        selectOnBlur={false}
        error={error}
        loading={isFetching}
        selection
        search
        options={this.optionsGenerator(suggestions)}
        multiple={false}
        onSearchChange={this.onSearchChange}
        value={selectedSuggestion}
        icon="search"
        placeholder={placeholder}
        onAddItem={this.handleAddItem}
        {...uiProps}
      />
    );
  }
}

SearchDropdown.propTypes = {
  fetchData: PropTypes.func.isRequired,
  placeholder: PropTypes.string,
  fieldPath: PropTypes.string,
  serializeSuggestions: PropTypes.func.isRequired,
  onAddItem: PropTypes.func,
  onChange: PropTypes.func,
  selectedSuggestion: PropTypes.any,
  debounceTime: PropTypes.number,
};

SearchDropdown.defaultProps = {
  debounceTime: 500,
  placeholder: i18next.t("Search..."),
};
