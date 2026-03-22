// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Clones} from "@openzeppelin/contracts/proxy/Clones.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

import {CauseToken} from "../token/CauseToken.sol";
import {ICauseTokenFactory} from "../interfaces/ICauseTokenFactory.sol";

/// @title CauseTokenFactory
/// @notice Deploys lightweight EIP-1167 minimal proxy clones of CauseToken.
/// @dev Each cause is identified by a `causeId` derived from `keccak256(abi.encodePacked(name))`.
///      Only addresses with CAUSE_CREATOR_ROLE (typically governance) can create new causes.
///
///      The factory stores a reference to the CauseToken implementation and clones it for each
///      new cause, dramatically reducing deployment gas costs.
contract CauseTokenFactory is ICauseTokenFactory, AccessControl {
    // ──────────────────────────────────────────────────────────────────────
    // Constants & Roles
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Role identifier for addresses permitted to create new causes.
    bytes32 public constant CAUSE_CREATOR_ROLE = keccak256("CAUSE_CREATOR_ROLE");

    // ──────────────────────────────────────────────────────────────────────
    // Storage
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Address of the CauseToken implementation contract used as the clone template.
    address public implementation;

    /// @notice Maps causeId => deployed CauseToken clone address.
    mapping(bytes32 => address) public causes;

    /// @notice Ordered list of all cause ids for enumeration.
    bytes32[] public causeIds;

    /// @notice Address that will be granted MINTER_ROLE on each new CauseToken.
    /// @dev Typically the ConversionEngine contract.
    address public minter;

    /// @dev Reverse lookup: cause token address => registered flag.
    mapping(address => bool) private _isCause;

    // ──────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────

    /// @notice Deploys the factory.
    /// @param implementation_ Address of the CauseToken implementation (template) contract.
    /// @param defaultAdmin    Address granted DEFAULT_ADMIN_ROLE and CAUSE_CREATOR_ROLE.
    /// @param minter_         Address granted MINTER_ROLE on each newly created cause token
    ///                        (typically the ConversionEngine).
    constructor(address implementation_, address defaultAdmin, address minter_) {
        if (implementation_ == address(0)) revert ZeroAddress();
        if (defaultAdmin == address(0)) revert ZeroAddress();
        if (minter_ == address(0)) revert ZeroAddress();

        implementation = implementation_;
        minter = minter_;

        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
        _grantRole(CAUSE_CREATOR_ROLE, defaultAdmin);
    }

    // ──────────────────────────────────────────────────────────────────────
    // External Functions
    // ──────────────────────────────────────────────────────────────────────

    /// @inheritdoc ICauseTokenFactory
    function createCause(
        string calldata name,
        string calldata symbol,
        string calldata causeName_,
        string calldata causeDescription,
        address charityWallet
    ) external onlyRole(CAUSE_CREATOR_ROLE) returns (address causeToken) {
        if (charityWallet == address(0)) revert ZeroAddress();

        // Derive a unique cause id from the token name.
        bytes32 _causeId = keccak256(abi.encodePacked(name));
        if (causes[_causeId] != address(0)) revert CauseAlreadyExists();

        // Deploy an EIP-1167 minimal proxy clone of the CauseToken implementation.
        causeToken = Clones.clone(implementation);

        // Initialize the clone with cause metadata and the minter address.
        CauseToken(causeToken).initialize(
            name,
            symbol,
            causeName_,
            causeDescription,
            charityWallet,
            _causeId,
            minter
        );

        // Register the cause.
        causes[_causeId] = causeToken;
        causeIds.push(_causeId);
        _isCause[causeToken] = true;

        emit CauseCreated(_causeId, causeToken, causeName_, charityWallet);
    }

    /// @inheritdoc ICauseTokenFactory
    function getCause(bytes32 causeId_) external view returns (address) {
        return causes[causeId_];
    }

    /// @inheritdoc ICauseTokenFactory
    function getAllCauses() external view returns (address[] memory) {
        uint256 len = causeIds.length;
        address[] memory result = new address[](len);
        for (uint256 i; i < len; ++i) {
            result[i] = causes[causeIds[i]];
        }
        return result;
    }

    /// @inheritdoc ICauseTokenFactory
    function isCause(address causeToken) external view returns (bool) {
        return _isCause[causeToken];
    }

    /// @inheritdoc ICauseTokenFactory
    function causeCount() external view returns (uint256) {
        return causeIds.length;
    }

    /// @notice Returns a paginated subset of cause token addresses.
    /// @param offset Starting index.
    /// @param limit Maximum number of results.
    /// @return result Array of cause token addresses.
    /// @return total Total number of causes.
    function getCausesPaginated(uint256 offset, uint256 limit)
        external
        view
        returns (address[] memory result, uint256 total)
    {
        total = causeIds.length;
        if (offset >= total) return (new address[](0), total);

        uint256 end = offset + limit;
        if (end > total) end = total;

        result = new address[](end - offset);
        for (uint256 i = offset; i < end; ++i) {
            result[i - offset] = causes[causeIds[i]];
        }
    }

    /// @notice Emitted when the minter address is updated.
    event MinterUpdated(address oldMinter, address newMinter);

    /// @notice Updates the minter address used for future cause token deployments.
    /// @param newMinter The new minter address (typically the ConversionEngine).
    function setMinter(address newMinter) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (newMinter == address(0)) revert ZeroAddress();
        address oldMinter = minter;
        minter = newMinter;
        emit MinterUpdated(oldMinter, newMinter);
    }
}
