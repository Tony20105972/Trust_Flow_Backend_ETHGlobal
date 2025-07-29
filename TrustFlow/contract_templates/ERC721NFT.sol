// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ERC721NFT {
    string public name = "DemoNFT";
    string public symbol = "DNFT";
    uint public totalSupply;
    mapping(uint => address) public ownerOf;

    event Mint(address indexed to, uint tokenId);

    function mint(address _to, uint _tokenId) public {
        require(ownerOf[_tokenId] == address(0), "Already minted");
        ownerOf[_tokenId] = _to;
        totalSupply++;
        emit Mint(_to, _tokenId);
    }
}
