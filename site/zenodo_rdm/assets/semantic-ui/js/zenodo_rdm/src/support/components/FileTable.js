import _get from "lodash/get";
import PropTypes from "prop-types";
import React from "react";
import {
    Icon,
    Table,
} from "semantic-ui-react";
import { humanReadableBytes } from "react-invenio-deposit";


const FileTable = ({ filesList, handleDelete, decimalSizeDisplay, negative }) => {
    return (
        <Table>
            <Table.Body>
                {filesList.map((file) => {
                    return (
                        <Table.Row key={file.name} negative={negative}>
                            <Table.Cell data-label="Filename" width={10}>
                                <>
                                    <label>{file.name}</label>
                                </>
                            </Table.Cell>
                            <Table.Cell data-label="Size" width={2}>
                                {file.size ? humanReadableBytes(file.size, decimalSizeDisplay) : ""}
                            </Table.Cell>
                
                            <Table.Cell textAlign="right" width={2}>
                                {negative ||
                                    <Icon
                                        link
                                        className="action primary"
                                        name="trash alternate outline"
                                        onClick={() => handleDelete(file)}
                                        aria-label={"Delete file"}
                                        title={"Delete file"}
                                    />
                                }
                            </Table.Cell>
                        </Table.Row>
                    );
                })}
            </Table.Body>
        </Table>)
}

FileTable.propTypes = {
    handleDelete: PropTypes.func.isRequired,
    filesList: PropTypes.array.isRequired,
    decimalSizeDisplay: PropTypes.bool,
    negative: PropTypes.bool,
};

FileTable.defaultProps = {
    decimalSizeDisplay: false,
    negative: false
};


export default FileTable;